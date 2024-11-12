import streamlit as st
from utils import render_footer

# Keep just the CSS and title
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
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title">NBA Player Statistics Explorer</div>', unsafe_allow_html=True)
st.write("Welcome to the NBA Stats Explorer! Use the sidebar to navigate between different features.")

# Add a brief description of each page
st.header("📑 Available Pages")

st.subheader("🏀 Live Games")
st.write("View live NBA game scores, stats, and leaders for today's games.")

st.subheader("📊 Player Statistics")
st.write("Explore historical player statistics with interactive filters and visualizations.")

st.subheader("🗺️ Team Map")
st.write("View NBA team locations across the United States.")

st.subheader("🏆 Playoff Race Calculator")
st.write("Calculate the playoff odds for each NBA team.")

render_footer()