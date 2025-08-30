import requests
import mysql.connector
import time
from datetime import datetime

# --- DB Connection ---
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123456789",
    database="cricketdb"
)
cursor = db.cursor()

# --- API Credentials and Base ---
BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com"
HEADERS = {
    "x-rapidapi-key": "3883e581ecmshcef93fbe41a5e04p1b0b4ejsn9b557e3dfd67",
    "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
}

def fetch_json(endpoint, params=None):
    url = f"{BASE_URL}{endpoint}"
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    if r.status_code == 200:
        return r.json()
    print(f"❌ {endpoint} -> {r.status_code}")
    return None

# --- Load teams (from matches or direct API) ---
def populate_teams():
    matches = fetch_json("/matches/v1/recent")
    team_ids = set()
    if not matches:
        return
    for tm in matches.get("typeMatches", []):
        for series_block in tm.get("seriesMatches", []):
            swrap = series_block.get("seriesAdWrapper", {})
            for game in swrap.get("matches", []):
                info = game.get("matchInfo", {}) or {}
                t1 = info.get("team1", {}) or {}
                t2 = info.get("team2", {}) or {}
                if t1:
                    team_ids.add((t1.get("teamId"), t1.get("teamName"), t1.get("teamSName")))
                if t2:
                    team_ids.add((t2.get("teamId"), t2.get("teamName"), t2.get("teamSName")))
    for tid, tname, sname in team_ids:
        if tid:
            cursor.execute("""
                INSERT IGNORE INTO teams (team_id, team_name, short_name, country)
                VALUES (%s, %s, %s, %s)
            """, (tid, tname, sname, tname))
    db.commit()
    print("✅ Teams populated")

# --- Load venues (from matches) ---
def populate_venues():
    matches = fetch_json("/matches/v1/recent")
    if not matches:
        return
    for tm in matches.get("typeMatches", []):
        for series_block in tm.get("seriesMatches", []):
            swrap = series_block.get("seriesAdWrapper", {})
            for game in swrap.get("matches", []):
                info = game.get("matchInfo", {}) or {}
                venue = (info.get("venueInfo") or {})
                venue_id = venue.get("id")
                venue_ground = venue.get("ground")
                venue_city = venue.get("city")
                venue_country = venue.get("country")
                cursor.execute("""
                    INSERT IGNORE INTO venues (venue_id, ground, city, country, capacity)
                    VALUES (%s,%s,%s,%s,%s)
                """, (venue_id, venue_ground, venue_city, venue_country, None))
    db.commit()
    print("✅ Venues populated")

# --- Load series (from series API) ---
def populate_series():
    data = fetch_json("/series/v1/international")
    if not data:
        return
    for bucket in data.get("seriesMapProto", []):
        for s in bucket.get("series", []):
            # Convert UNIX milli to date
            start_dt = int(s.get("startDt", "0")) // 1000 if s.get("startDt") else 0
            end_dt = int(s.get("endDt", "0")) // 1000 if s.get("endDt") else 0
            start_date = datetime.utcfromtimestamp(start_dt).date() if start_dt else None
            end_date = datetime.utcfromtimestamp(end_dt).date() if end_dt else None
            cursor.execute("""
                INSERT IGNORE INTO series (series_id, name, start_date, end_date, host_country, match_type, total_matches)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                s.get("id"),
                s.get("name"),
                start_date,
                end_date,
                None,
                None,
                None
            ))
    db.commit()
    print("✅ Series populated")

# --- Load matches (from matches API) ---
def populate_matches():
    matches = fetch_json("/matches/v1/recent")
    if not matches:
        return
    for tm in matches.get("typeMatches", []):
        for series_block in tm.get("seriesMatches", []):
            swrap = series_block.get("seriesAdWrapper", {})
            series_id = swrap.get("seriesId")
            for game in swrap.get("matches", []):
                info = game.get("matchInfo", {}) or {}
                match_id = info.get("matchId")
                t1 = info.get("team1", {}) or {}
                t2 = info.get("team2", {}) or {}
                team1_id = t1.get("teamId") or t1.get("id")
                team2_id = t2.get("teamId") or t2.get("id")
                venue = (info.get("venueInfo") or {})
                venue_id = venue.get("id")
                match_format = info.get("matchFormat")
                match_desc = info.get("matchDesc")
                start_date = int(info.get("startDate", "0")) // 1000 if info.get("startDate") else 0
                status = info.get("status")
                winner_id = None
                result_margin = None
                result_type = None
                # Simple winner parsing (refine as needed for your context)
                if status and "won by" in status:
                    if "runs" in status:
                        result_type = "runs"
                        parts = status.split("won by")
                        margin = parts[1].strip().split()[0]
                        result_margin = int(''.join([c for c in margin if c.isdigit()]))
                    elif "wkt" in status or "wickets" in status:
                        result_type = "wickets"
                        parts = status.split("won by")
                        margin = parts[1].strip().split()[0]
                        result_margin = int(''.join([c for c in margin if c.isdigit()]))
                cursor.execute("""
                    INSERT IGNORE INTO matches 
                    (match_id, series_id, team1_id, team2_id, venue_id, match_format, match_desc, start_date, status, winner_id, result_margin, result_type, toss_winner_id, toss_decision)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,FROM_UNIXTIME(%s),%s,%s,%s,%s,NULL,NULL)
                """, (
                    match_id, series_id, team1_id, team2_id, venue_id,
                    match_format, match_desc, start_date,
                    status, winner_id, result_margin, result_type
                ))
    db.commit()
    print("✅ Matches populated")

# --- Load players (from /teams/v1/{team_id}/players API) ---
def populate_players():
    cursor.execute("SELECT team_id FROM teams")
    team_ids = [r[0] for r in cursor.fetchall()]
    for team_id in team_ids:
        data = fetch_json(f"/teams/v1/{team_id}/players")
        if not data:
            continue
        for p in data.get("player", []):
            if "id" not in p: continue  # skip headers like {"name": "BATSMEN"}
            pid = int(p.get("id"))
            pname = p.get("name")
            batstyle = p.get("battingStyle", None)
            bowlstyle = p.get("bowlingStyle", None)
            cursor.execute("""
                INSERT INTO players (player_id, name, playing_role, batting_style, bowling_style, team_id)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE name=VALUES(name), batting_style=VALUES(batting_style), bowling_style=VALUES(bowling_style), team_id=VALUES(team_id)
            """, (pid, pname, None, batstyle, bowlstyle, team_id))
        db.commit()
        time.sleep(0.5)
    print("✅ Players populated")

# --- Main Execution ---
if __name__ == "__main__":
    populate_teams()
    populate_venues()
    populate_series()
    populate_matches()
    populate_players()
    print("🎉 Database loaded")
