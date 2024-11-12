import streamlit as st
import pandas as pd
from nba_api.stats.endpoints import leagueleaders
from nba_api.stats.static import teams, players

@st.cache_data
def fetch_nba_data(season):
    # Get league leaders data
    league_leaders = leagueleaders.LeagueLeaders(season=season)
    df = league_leaders.get_data_frames()[0]
    
    # Get players data for names if needed
    players_df = pd.DataFrame(players.get_players())
    
    # Merge only if you need additional player information
    df = df.merge(
        players_df[['id', 'full_name']],
        left_on='PLAYER_ID',
        right_on='id',
        how='left'
    )
    
    return df

@st.cache_data
def fetch_teams():
    return pd.DataFrame(teams.get_teams())

@st.cache_data
def fetch_players():
    return pd.DataFrame(players.get_players())

def render_footer():
    st.markdown(
        """
        <style>
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #f8f9fa;
            padding: 10px;
            text-align: center;
            border-top: 1px solid #ddd;
        }
        </style>
        <div class="footer">Data sourced from NBA API | Built with ❤️ using Streamlit</div>
        """,
        unsafe_allow_html=True
    )