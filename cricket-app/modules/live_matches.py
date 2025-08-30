# modules/live_matches.py
import requests
import streamlit as st
import pandas as pd

def run():
    def get_rapidapi_headers():
        return {
            "x-rapidapi-key": st.secrets["RAPIDAPI_KEY"],
            "x-rapidapi-host": st.secrets.get("RAPIDAPI_HOST", "cricbuzz-cricket.p.rapidapi.com")
        }

    def rapidapi_base():
        return st.secrets.get("RAPIDAPI_BASE", "https://cricbuzz-cricket.p.rapidapi.com")

    def fetch_live_matches():
        url = f"{rapidapi_base()}/matches/v1/live"
        headers = get_rapidapi_headers()
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def flatten_matches(data: dict):
        result = []
        for type_block in data.get("typeMatches", []):
            for series_block in type_block.get("seriesMatches", []):
                series = series_block.get("seriesAdWrapper") or {}
                series_name = series.get("seriesName")
                matches = series.get("matches", [])
                for m in matches:
                    info = m.get("matchInfo", {})
                    result.append({
                        "matchId": info.get("matchId"),
                        "series": series_name,
                        "desc": info.get("matchDesc"),
                        "teams": f"{info.get('team1',{}).get('teamName')} vs {info.get('team2',{}).get('teamName')}",
                        "venue": (info.get("venueInfo") or {}).get("ground"),
                    })
        return result

    def fetch_scorecard(match_id: int):
        url = f"{rapidapi_base()}/mcenter/v1/{match_id}/scard"
        headers = get_rapidapi_headers()
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        return resp.json()

    st.title("⚡ Live Match Dashboard")

    try:
        data = fetch_live_matches()
        matches = flatten_matches(data)
    except Exception as e:
        st.error(f"Error fetching matches: {e}")
        return

    if not matches:
        st.info("🚫 No live matches at the moment.")
        return

    match_names = [f"{m['teams']} — {m['desc']}" for m in matches]
    selected_match = st.selectbox("Select a live match", match_names)

    chosen = matches[match_names.index(selected_match)]
    st.subheader(f"🏟 {chosen['teams']} — {chosen['desc']}")
    st.caption(f"Series: {chosen['series']} | Venue: {chosen['venue']}")

    try:
        scard = fetch_scorecard(chosen["matchId"])

        # ✅ Correct: data is under "scorecard"
        for inng in scard.get("scorecard", []):
            team = inng.get("batteamname")
            score = inng.get("score")
            wickets = inng.get("wickets")
            overs = inng.get("overs")

            st.markdown(f"### 🏏 {team}: {score}/{wickets} in {overs} overs")

            # ---- Batting ----
            batsmen = inng.get("batsman", [])
            if batsmen:
                bat_df = pd.DataFrame([{
                    "Batsman": b.get("name"),
                    "Runs": b.get("runs"),
                    "Balls": b.get("balls"),
                    "4s": b.get("fours"),
                    "6s": b.get("sixes"),
                    "SR": b.get("strkrate"),
                    "Dismissal": b.get("outdec")
                } for b in batsmen])
                st.write("**Batting**")
                st.table(bat_df)

            # ---- Bowling ----
            bowlers = inng.get("bowler", [])
            if bowlers:
                bowl_df = pd.DataFrame([{
                    "Bowler": b.get("name"),
                    "Overs": b.get("overs"),
                    "Runs": b.get("runs"),
                    "Wickets": b.get("wickets"),
                    "Econ": b.get("economy")
                } for b in bowlers])
                st.write("**Bowling**")
                st.table(bowl_df)

    except Exception as e:
        st.warning(f"Could not fetch scorecard for match {chosen['matchId']}: {e}")
