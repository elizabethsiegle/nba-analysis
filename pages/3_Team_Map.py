import streamlit as st
import folium
from streamlit_folium import st_folium
from utils import render_footer

# Folium Map Visualization
st.subheader("NBA Teams Map")
nba_map = folium.Map(location=[37.0902, -95.7129], zoom_start=4)  # Center on the USA

# Add team locations to the map
team_locations = {
    'Lakers': [34.0522, -118.2437],
    'Warriors': [37.7749, -122.4194],
    'Nets': [40.6824, -73.9750],
    'Bucks': [43.0389, -87.9065],
    '76ers': [39.9526, -75.1652],
    'Mavericks': [32.7767, -96.7970],
    # Add more teams as needed
}

for team, coordinates in team_locations.items():
    folium.Marker(
        location=coordinates,
        popup=f"<b>{team}</b>",
        icon=folium.Icon(color="blue", icon="info-sign"),
    ).add_to(nba_map)

# Display map in Streamlit
st_folium(nba_map, width=700, height=400)

render_footer()