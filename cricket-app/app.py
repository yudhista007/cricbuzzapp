# app.py
import streamlit as st
import importlib

st.set_page_config(page_title="Cricket Analytics", page_icon="🏏", layout="wide")

# Sidebar Navigation
st.sidebar.title("🏏 Cricket Analytics")
page = st.sidebar.selectbox(
    "Select Page",
    ["🏠 Home", "⚡ Live Matches", "👤 Player Status", "🔍 SQL Analytics", "🛠️ CRUD Operations"]
)

# Simple Home Page
if page == "🏠 Home":
    st.title("🏏 Cricket Analytics Dashboard")
    st.markdown("""
    Welcome! Use the sidebar to explore different features:
    - ⚡ **Live Matches** – See current live fixtures & scorecards  
    - 👤 **Player Status** – Explore player profiles and stats  
    - 🔍 **SQL Analytics** – Run queries on stats database  
    - 🛠️ **CRUD Operations** – Manage player stats  
    """)

elif page == "⚡ Live Matches":
    live_matches = importlib.import_module("modules.live_matches")  # ✅ renamed folder
    live_matches.run()

elif page == "👤 Player Status":
    player_status = importlib.import_module("modules.player_status")
    player_status.run()

elif page == "🔍 SQL Analytics":
    sql_analysis = importlib.import_module("modules.sql_analysis")
    sql_analysis.run()

elif page == "🛠️ CRUD Operations":
    page4_crud = importlib.import_module("modules.page4_crud")
    page4_crud.run()
