import streamlit as st
import requests
import pandas as pd

API_KEY = "61cfef2a6amsh0e3aa8ef5a2cdd2p164bd4jsn50650f8c941d"
API_HOST = "cricbuzz-cricket.p.rapidapi.com"

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST
}

BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com"

def search_player(name):
    url = f"{BASE_URL}/stats/v1/player/search"
    params = {"plrN": name}
    res = requests.get(url, headers=HEADERS, params=params)
    return res.json()

def get_profile(player_id):
    url = f"{BASE_URL}/stats/v1/player/{player_id}"
    return requests.get(url, headers=HEADERS).json()

def get_batting(player_id):
    url = f"{BASE_URL}/stats/v1/player/{player_id}/batting"
    return requests.get(url, headers=HEADERS).json()

def get_bowling(player_id):
    url = f"{BASE_URL}/stats/v1/player/{player_id}/bowling"
    return requests.get(url, headers=HEADERS).json()

def format_batbowl(data):
    """Convert Cricbuzz stats format into dataframe"""
    if not data or "headers" not in data or "values" not in data:
        return None
    
    headers = data["headers"]
    rows = [row["values"] for row in data["values"]]
    return pd.DataFrame(rows, columns=headers)

# ---------- Page Runner ----------
def run():
    st.title("🏏 Player Status Page")

    player_name = st.text_input("Enter Player Name")

    if player_name:
        results = search_player(player_name)

        if "player" in results and results["player"]:
            players = {f"{p['name']} ({p['teamName']})": p["id"] for p in results["player"]}
            selected = st.selectbox("Select a Player", list(players.keys()))

            if selected:
                player_id = players[selected]

                # Fetch profile, batting, bowling
                profile = get_profile(player_id)
                batting = get_batting(player_id)
                bowling = get_bowling(player_id)

                # Player Profile
                st.subheader("👤 Player Profile")
                st.write(f"**Name:** {profile.get('name')}")
                st.write(f"**Country:** {profile.get('country')}")
                st.write(f"**Date of Birth:** {profile.get('DoB')}")
                st.write(f"**Role:** {profile.get('role')}")
                if profile.get("imageId"):
                    st.image(f"https://cricbuzz-cricket.p.rapidapi.com/img/v1/i1/c{profile['imageId']}/i.jpg")

                # Batting Stats
                st.subheader("🏏 Batting Stats")
                df_batting = format_batbowl(batting)
                if df_batting is not None:
                    st.dataframe(df_batting, use_container_width=True)
                else:
                    st.write("No batting data available")

                # Bowling Stats
                st.subheader("🎯 Bowling Stats")
                df_bowling = format_batbowl(bowling)
                if df_bowling is not None:
                    st.dataframe(df_bowling, use_container_width=True)
                else:
                    st.write("No bowling data available")

                # Cricbuzz profile link
                st.markdown(
                    f"🔗 [View Full Profile on Cricbuzz](https://www.cricbuzz.com/profiles/{player_id})",
                    unsafe_allow_html=True
                )
        else:
            st.warning("No players found. Try another name.")
