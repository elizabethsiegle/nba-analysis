import streamlit as st
from dotenv import load_dotenv
from langchain_community.llms.cloudflare_workersai import CloudflareWorkersAI
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnablePassthrough
import os
from nba_api.stats.endpoints import leaguestandings, teamgamelog
from nba_api.stats.static import teams
import plotly.graph_objects as go
from utils import render_footer

load_dotenv()

# Add custom CSS
st.markdown(
    """
    <style>
    /* Main title styling */
    .title {
        color: #FFFFFF;
        padding: 20px;
        text-align: center;
        background: linear-gradient(to right, #1e3799, #4a69bd, #1e3799);
        border-radius: 10px;
        margin-bottom: 30px;
    }
    
    /* Conference selector styling */
    div[role="radiogroup"] {
        background-color: #2c3e50;
        padding: 15px;
        border-radius: 10px;
        color: white;
    }
    
    /* Subheader styling */
    h2 {
        color: #FFFFFF;
        border-left: 5px solid #3498db;
        padding-left: 10px;
        margin: 30px 0 20px 0;
    }
    
    /* Slider styling */
    [data-testid="stSlider"] {
        padding: 20px;
        margin: 20px 0;
    }
    
    /* Team selection box styling */
    [data-testid="stSelectbox"] {
        border-radius: 10px;
        padding: 5px;
        margin: 10px 0;
    }
    
    /* Status messages styling */
    .stSuccess, .stInfo, .stWarning, .stError {
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        font-weight: 500;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<h1 class="title">🏀 NBA Playoff Race Calculator</h1>', unsafe_allow_html=True)

# Helper function to find team by city
def find_team_by_city(city):
    """Find team ID by city name"""
    nba_teams = teams.get_teams()
    for team in nba_teams:
        if team['city'] == city:
            return team
    return None

# Cache the standings data
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_current_standings():
    standings = leaguestandings.LeagueStandings()
    df = standings.get_data_frames()[0]
    
    # Rename columns to match our needs
    df['WINS'] = df['Oct'].str.split('-').str[0].astype(int) + df['Nov'].str.split('-').str[0].astype(int)
    df['LOSSES'] = df['Oct'].str.split('-').str[1].astype(int) + df['Nov'].str.split('-').str[1].astype(int)
    
    # Calculate win percentage
    df['WinPCT'] = df['WINS'] / (df['WINS'] + df['LOSSES'])
    
    # Get L10 from PreAS (Pre All-Star) record
    df['L10'] = df['PreAS']
    
    # Clean up conference names
    df['Conference'] = df['Conference'].map({'East': 'Eastern', 'West': 'Western'})
    
    return df[['TeamCity', 'TeamName', 'WINS', 'LOSSES', 'WinPCT', 'L10', 'Conference', 'PlayoffRank']]

# Cache remaining games data
@st.cache_data(ttl=3600)
def get_remaining_games(team_id):
    game_log = teamgamelog.TeamGameLog(team_id=team_id, season_type_all_star='Regular Season').get_data_frames()[0]
    total_games = 82
    remaining_games = total_games - len(game_log)
    return remaining_games

def calculate_playoff_odds(current_wins, current_losses, remaining_games, win_probability):
    total_possible_outcomes = 2 ** remaining_games
    favorable_outcomes = 0
    
    # Calculate playoff threshold (usually around 43-45 wins in an 82-game season)
    playoff_threshold = 43
    
    for scenario in range(total_possible_outcomes):
        additional_wins = bin(scenario).count('1')
        additional_losses = remaining_games - additional_wins
        
        # Calculate probability of this scenario
        scenario_probability = (
            win_probability ** additional_wins *
            (1 - win_probability) ** additional_losses
        )
        
        final_wins = current_wins + additional_wins
        if final_wins >= playoff_threshold:
            favorable_outcomes += scenario_probability
            
    return favorable_outcomes * 100  # Convert to percentage

# Get current standings
try:
    standings_df = get_current_standings()
    
    # Create conference selections
    st.subheader("Select Conference")
    conference = st.radio(
        label="Conference Selection",
        options=["Eastern", "Western"],
        label_visibility="collapsed"
    )
    
    # Filter standings by conference
    conf_standings = standings_df[standings_df['Conference'] == conference]
    
    # Sort by wins and playoff rank
    conf_standings = conf_standings.sort_values(['WINS', 'PlayoffRank'], ascending=[False, True])
    
    # Display current standings
    st.subheader(f"Current {conference} Conference Standings")
    
    # Create a more visually appealing standings table
    standings_display = conf_standings[['TeamCity', 'TeamName', 'WINS', 'LOSSES', 'WinPCT', 'L10']].copy()
    standings_display.loc[:, 'Team'] = standings_display['TeamCity'] + ' ' + standings_display['TeamName']
    standings_display = standings_display.drop(['TeamCity', 'TeamName'], axis=1)
    standings_display = standings_display[['Team', 'WINS', 'LOSSES', 'WinPCT', 'L10']]
    
    # Update the playoff position highlighting function
    def highlight_playoff_position(row):
        if row.name < 6:  # Guaranteed playoff spot
            return ['background-color: rgba(168, 230, 207, 0.8)'] * len(row)  # Semi-transparent green
        elif row.name < 8:  # Likely playoff spot
            return ['background-color: rgba(220, 237, 193, 0.8)'] * len(row)  # Semi-transparent yellow-green
        elif row.name < 10:  # Play-in tournament
            return ['background-color: rgba(255, 211, 182, 0.8)'] * len(row)  # Semi-transparent orange
        return ['background-color: rgba(255, 170, 165, 0.8)'] * len(row)  # Semi-transparent red
    
    st.dataframe(standings_display.style.apply(highlight_playoff_position, axis=1))
    
    # Team selection for detailed analysis
    st.subheader("Analyze Team's Playoff Chances")
    selected_team = st.selectbox(
        "Select a team to analyze",
        options=conf_standings['TeamCity'] + ' ' + conf_standings['TeamName']
    )
    
    if selected_team:
        team_data = conf_standings[
            (conf_standings['TeamCity'] + ' ' + conf_standings['TeamName']) == selected_team
        ].iloc[0]
        
        # Get remaining games
        team_info = find_team_by_city(team_data['TeamCity'])
        if team_info:
            team_id = team_info['id']
            remaining = get_remaining_games(team_id)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Wins", int(team_data['WINS']))
            with col2:
                st.metric("Current Losses", int(team_data['LOSSES']))
            with col3:
                st.metric("Remaining Games", remaining)
            
            # Win probability slider
            st.subheader("Projected Win Probability")
            win_prob = st.slider(
                "Estimated win probability for remaining games",
                min_value=0.0,
                max_value=1.0,
                value=float(team_data['WinPCT']),
                step=0.05
            )
            
            # Calculate and display playoff odds
            if remaining > 0:
                odds = calculate_playoff_odds(
                    team_data['WINS'],
                    team_data['LOSSES'],
                    remaining,
                    win_prob
                )
                
                # Create a gauge chart for playoff odds
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=odds,
                    title={'text': "Playoff Chances", 'font': {'size': 24, 'color': '#FFFFFF'}},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#FFFFFF"},
                        'bar': {'color': "#3498db"},
                        'bgcolor': "rgba(0,0,0,0)",
                        'borderwidth': 2,
                        'bordercolor': "#FFFFFF",
                        'steps': [
                            {'range': [0, 20], 'color': "#ff6b6b"},
                            {'range': [20, 40], 'color': "#ffd93d"},
                            {'range': [40, 60], 'color': "#6c5ce7"},
                            {'range': [60, 80], 'color': "#a8e6cf"},
                            {'range': [80, 100], 'color': "#00b894"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 50
                        }
                    }
                ))
                
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font={'color': '#FFFFFF'}
                )
                
                st.plotly_chart(fig)
                
                # Add analysis text
                if odds >= 90:
                    st.success(f"🎉 {selected_team} has an excellent chance of making the playoffs!")
                elif odds >= 70:
                    st.info(f"👍 {selected_team} is likely to make the playoffs.")
                elif odds >= 40:
                    st.warning(f"😅 {selected_team} is in the playoff bubble - every game counts!")
                else:
                    st.error(f"😟 {selected_team} faces an uphill battle to make the playoffs.")
                
                # Show potential final records
                st.subheader("Potential Final Records")
                best_case = team_data['WINS'] + remaining
                worst_case = team_data['WINS']
                expected_wins = team_data['WINS'] + (remaining * win_prob)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Best Case", f"{best_case}-{team_data['LOSSES']}")
                with col2:
                    st.metric("Expected", f"{int(expected_wins)}-{int(team_data['LOSSES'] + (remaining * (1-win_prob)))}")
                with col3:
                    st.metric("Worst Case", f"{worst_case}-{team_data['LOSSES'] + remaining}")
            
            else:
                st.info("Regular season is complete for this team.")
        else:
            st.error(f"Could not find team ID for {team_data['TeamCity']}")
        # Add AI Analysis section
        st.subheader("🤖 AI Analysis")
        
        # Initialize the LLM and conversation chain
        @st.cache_resource
        def initialize_chat(team_data, standings_data):
            llm = CloudflareWorkersAI(
                account_id=os.getenv('CLOUDFLARE_ACCOUNT_ID'),
                api_token=os.getenv('CLOUDFLARE_API_TOKEN'),
                model="@cf/meta/llama-2-7b-chat-int8"
            )
            
            # Create context from team and standings data
            team_context = f"""
            Team: {selected_team}
            Current Record: {team_data['WINS']}-{team_data['LOSSES']}
            Win Percentage: {team_data['WinPCT']:.3f}
            Games Remaining: {remaining}
            Conference: {conference}
            Current Position: {team_data['PlayoffRank']}
            
            Conference Standings:
            {standings_display.to_string()}
            """

            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert NBA analyst specializing in playoff predictions and team analysis. 
                Provide detailed insights about teams' playoff chances, considering their current record, 
                remaining schedule, and historical performance.
                
                Current team context:
                {team_context}
                
                Provide specific, data-driven analysis while maintaining an engaging tone."""),
                ("human", "{input}"),
                ("ai", "{agent_scratchpad}")
            ])

            memory = ConversationBufferMemory(return_messages=True, output_key="agent_scratchpad")
            
            def get_chat_history(inputs):
                return memory.chat_memory.messages

            chain = (
                RunnablePassthrough.assign(
                    agent_scratchpad=get_chat_history,
                    team_context=lambda _: team_context
                )
                | prompt
                | llm
            )

            return chain, memory

        # Initialize chat
        chain, memory = initialize_chat(team_data, standings_display)

        # Create the chat interface
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask about the team's playoff chances..."):
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Generate AI response
            with st.chat_message("assistant"):
                response = chain.invoke({"input": prompt})
                st.markdown(response)
                
            # Add AI response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

        # Add suggested questions
        st.markdown("### Suggested Questions")
        questions = [
            "What are the key factors affecting their playoff chances?",
            "How does their remaining schedule look?",
            "What improvements do they need to make to secure a playoff spot?",
            "How do they compare to other teams in the playoff race?",
            "What's their projected final record?"
        ]
        
        for q in questions:
            if st.button(q):
                # Simulate clicking the chat input with this question
                with st.chat_message("user"):
                    st.markdown(q)
                st.session_state.messages.append({"role": "user", "content": q})
                
                with st.chat_message("assistant"):
                    response = chain.invoke({"input": q})
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Add some space before the footer
    st.markdown("<br><br>", unsafe_allow_html=True)

    render_footer()

except Exception as e:
    st.error(f"Error fetching data: {str(e)}")
    st.info("Please try again later or contact support if the problem persists.")

