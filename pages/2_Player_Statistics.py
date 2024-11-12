import streamlit as st
import pandas as pd
import plotly.express as px
from nba_api.stats.library.parameters import SeasonAll
from utils import fetch_nba_data, fetch_teams, render_footer

# CSS for styling
st.markdown(
    """
    <style>
        .title {
            font-size: 2em;
            color: #FF5733;
            font-weight: bold;
            text-align: center;
            margin-top: -20px;
        }
        .dropdown {
            font-size: 1em;
            margin-bottom: 10px;
        }
        .footer {
            position: fixed;
            bottom: 0;
            width: 100%;
            color: grey;
            text-align: center;
            padding: 10px;
            font-size: 0.8em;
        }
        .game-container {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .team-name {
            font-size: 1.4em;
            font-weight: bold;
            margin-bottom: 5px;
            color: #1f77b4;
        }
        .team-score {
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }
        .team-record {
            color: #666;
            font-size: 0.9em;
        }
        .game-status {
            text-align: center;
            font-size: 1.2em;
            color: #e74c3c;
            font-weight: bold;
        }
        .game-time {
            text-align: center;
            color: #7f8c8d;
        }
        .game-leaders {
            background-color: #fff;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
        }
        .refresh-button {
            background-color: #2ecc71;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-align: center;
            margin: 20px 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Layout title
st.markdown('<div class="title">NBA Player Statistics Explorer</div>', unsafe_allow_html=True)
st.write("Use the dropdown filters to explore player stats by season, team, or position.")

# Dropdowns for season, team, and position
season_list = ['2023-24', '2022-23', '2021-22', '2020-21', '2019-20']
season_list.append(SeasonAll.default)  # Add 'ALL TIME' option
season = st.selectbox("Select Season", options=season_list)
team_data = fetch_teams()
team_filter = st.selectbox("Select Team", options=["All Teams"] + team_data['full_name'].unique().tolist())
# position_filter = st.selectbox("Select Position", options=["All Positions", "Guard", "Forward", "Center"])

# Fetch data based on selected season
df = fetch_nba_data(season)

# Add informational text when viewing all-time stats
if season == SeasonAll.default:
    st.info("Showing all-time NBA statistics. This may take a moment to load.")

# Calculate per game averages
df['PPG'] = df['PTS'] / df['GP']
df['RPG'] = df['REB'] / df['GP']  # Rebounds Per Game
df['APG'] = df['AST'] / df['GP']  # Assists Per Game

# Filter by team
if team_filter != "All Teams":
    team_id = team_data[team_data['full_name'] == team_filter]['id'].values[0]
    df = df[df['TEAM_ID'] == team_id]

# Display the filtered data
st.subheader("Filtered NBA Player Stats")
st.dataframe(df[['PLAYER', 'TEAM', 'PPG', 'RPG', 'APG']])  # Show per game stats

if not df.empty:
    # Create two columns for chart layout
    col1, col2 = st.columns(2)
    
    with col1:
        # Scatter plot of PPG vs RPG with APG as bubble size
        st.subheader("Points vs Rebounds (Size = Assists)")
        scatter = px.scatter(
            df,
            x='PPG',
            y='RPG',
            size='APG',
            hover_name='PLAYER',
            hover_data=['TEAM'],
            title="Points vs Rebounds Performance",
            labels={'PPG': 'Points Per Game', 'RPG': 'Rebounds Per Game'},
            width=600,
            height=500
        )
        st.plotly_chart(scatter)

    with col2:
        # Radar chart for top 5 players by PPG
        st.subheader("Top 5 Players Performance Radar")
        top_5_players = df.nlargest(5, 'PPG')
        radar_data = top_5_players[['PLAYER', 'PPG', 'RPG', 'APG']]
        
        radar = px.line_polar(
            radar_data.melt(id_vars=['PLAYER']),
            r='value',
            theta='variable',
            line_close=True,
            color='PLAYER',
            title="Top 5 Players Performance Comparison",
            width=600,
            height=500
        )
        st.plotly_chart(radar)

    # Add interactive player comparison
    st.subheader("Player Comparison Tool")
    col1, col2 = st.columns(2)
    with col1:
        player1 = st.selectbox("Select Player 1", options=df['PLAYER'].unique())
    with col2:
        player2 = st.selectbox("Select Player 2", options=df['PLAYER'].unique())

    if player1 and player2:
        comparison_df = df[df['PLAYER'].isin([player1, player2])]
        comparison_stats = ['PPG', 'RPG', 'APG']
        
        # Bar chart comparison
        comparison_melted = comparison_df.melt(
            id_vars=['PLAYER'],
            value_vars=comparison_stats,
            var_name='Stat',
            value_name='Value'
        )
        
        comparison_chart = px.bar(
            comparison_melted,
            x='Stat',
            y='Value',
            color='PLAYER',
            barmode='group',
            title=f"Player Comparison: {player1} vs {player2}",
            labels={'Value': 'Per Game Average'},
            width=800,
            height=400
        )
        st.plotly_chart(comparison_chart)

    # Add statistical distribution plots
    st.subheader("Statistical Distributions")
    stat_to_view = st.selectbox(
        "Select Statistic to View Distribution",
        options=['PPG', 'RPG', 'APG']
    )
    
    col1, col2 = st.columns(2)
    with col1:
        # Box plot
        box_plot = px.box(
            df,
            y=stat_to_view,
            title=f"{stat_to_view} Distribution",
            width=600,
            height=400
        )
        st.plotly_chart(box_plot)
    
    with col2:
        # Histogram
        histogram = px.histogram(
            df,
            x=stat_to_view,
            title=f"{stat_to_view} Histogram",
            width=600,
            height=400
        )
        st.plotly_chart(histogram)

    # Add team performance summary
    if team_filter != "All Teams":
        st.subheader(f"{team_filter} Team Summary")
        team_stats = {
            'Average PPG': df['PPG'].mean(),
            'Average RPG': df['RPG'].mean(),
            'Average APG': df['APG'].mean(),
            'Max PPG': df['PPG'].max(),
            'Max RPG': df['RPG'].max(),
            'Max APG': df['APG'].max(),
        }
        
        # Create metrics display
        col1, col2, col3 = st.columns(3)
        col1.metric("Team PPG", f"{team_stats['Average PPG']:.1f}", f"Max: {team_stats['Max PPG']:.1f}")
        col2.metric("Team RPG", f"{team_stats['Average RPG']:.1f}", f"Max: {team_stats['Max RPG']:.1f}")
        col3.metric("Team APG", f"{team_stats['Average APG']:.1f}", f"Max: {team_stats['Max APG']:.1f}")


render_footer()