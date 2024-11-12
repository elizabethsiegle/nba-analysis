import streamlit as st
from nba_api.live.nba.endpoints import scoreboard
from utils import render_footer

# Add Live Games Section
st.header("🏀 Live NBA Games")

try:
    games_data = scoreboard.ScoreBoard()
    games_dict = games_data.get_dict()
    
    if 'scoreboard' in games_dict and 'games' in games_dict['scoreboard']:
        games = games_dict['scoreboard']['games']
        
        # Add refresh button at the top
        col1, col2, col3 = st.columns([2,1,2])
        with col2:
            if st.button("🔄 Refresh Scores", key="refresh_top"):
                st.experimental_rerun()
        
        for game in games:
            st.markdown('<div class="game-container">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([2,1,2])
            
            # Away Team
            with col1:
                st.markdown(f'<div class="team-name">{game["awayTeam"]["teamCity"]} {game["awayTeam"]["teamName"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="team-score">{game["awayTeam"]["score"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="team-record">({game["awayTeam"]["wins"]}-{game["awayTeam"]["losses"]})</div>', unsafe_allow_html=True)
            
            # Game Status
            with col2:
                status_color = {
                    1: "#2ecc71",  # Upcoming - Green
                    2: "#e74c3c",  # Live - Red
                    3: "#7f8c8d"   # Final - Gray
                }[game['gameStatus']]
                
                st.markdown(f'<div class="game-status" style="color: {status_color}">{game["gameStatusText"]}</div>', unsafe_allow_html=True)
                
                if game['gameStatus'] == 1:
                    st.markdown('<div class="game-time">🔜 Upcoming</div>', unsafe_allow_html=True)
                elif game['gameStatus'] == 2:
                    st.markdown('<div class="game-time">🏀 LIVE</div>', unsafe_allow_html=True)
                    if game['period'] > 0:
                        st.markdown(f'<div class="game-time">Q{game["period"]}</div>', unsafe_allow_html=True)
                        if game['gameClock']:
                            st.markdown(f'<div class="game-time">{game["gameClock"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="game-time">✅ Final</div>', unsafe_allow_html=True)
            
            # Home Team
            with col3:
                st.markdown(f'<div class="team-name" style="text-align: right">{game["homeTeam"]["teamCity"]} {game["homeTeam"]["teamName"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="team-score" style="text-align: right">{game["homeTeam"]["score"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="team-record" style="text-align: right">({game["homeTeam"]["wins"]}-{game["homeTeam"]["losses"]})</div>', unsafe_allow_html=True)
            
            # Game Leaders
            if game['gameStatus'] > 1 and 'gameLeaders' in game:
                leaders = game['gameLeaders']
                if leaders['homeLeaders']['name'] or leaders['awayLeaders']['name']:
                    with st.expander("📊 Game Leaders"):
                        st.markdown('<div class="game-leaders">', unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**{game['awayTeam']['teamCity']} Leader:**")
                            st.write(f"👤 {leaders['awayLeaders']['name']}")
                            st.write(f"📈 {leaders['awayLeaders']['points']} PTS | {leaders['awayLeaders']['rebounds']} REB | {leaders['awayLeaders']['assists']} AST")
                        with col2:
                            st.markdown(f"**{game['homeTeam']['teamCity']} Leader:**")
                            st.write(f"👤 {leaders['homeLeaders']['name']}")
                            st.write(f"📈 {leaders['homeLeaders']['points']} PTS | {leaders['homeLeaders']['rebounds']} REB | {leaders['homeLeaders']['assists']} AST")
                        st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No games scheduled for today.")
        
except Exception as e:
    st.error(f"Unable to fetch live game data. Error: {str(e)}")
    st.info("This might happen if there are no games today or if the NBA API is unavailable.")

render_footer()