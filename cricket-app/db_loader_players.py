import requests
import mysql.connector

# --- DB Connection ---
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123456789",
    database="cricketdb"
)
cursor = db.cursor()

# --- API Base ---
BASE_URL = "https://cricbuzz-cricket.p.rapidapi.com"
HEADERS = {
    "x-rapidapi-key": "3883e581ecmshcef93fbe41a5e04p1b0b4ejsn9b557e3dfd67",  # Use your key
    "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
}

# --- Load trending players ---
def load_trending_players():
    url = f"{BASE_URL}/stats/v1/player/trending"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print("❌ Failed to fetch trending players")
        return
    data = response.json()
    players = data.get("player", [])
    if not players:
        print("⚠️ No trending players found")
        return

    for p in players:
        pid = p.get("id")
        name = p.get("name", "")
        # teamName = p.get("teamName", "")  # Not used in table
        team_id = None  # As trending API does not give team_id
        # Fetch full details for proper player attributes
        details_url = f"{BASE_URL}/stats/v1/player/{pid}"
        details_resp = requests.get(details_url, headers=HEADERS)
        if details_resp.status_code != 200:
            print(f"❌ Failed to fetch player details for {name}")
            continue
        details = details_resp.json()
        role = details.get("role", "")
        batting = details.get("bat", "")
        bowling = details.get("bowl", "")

        cursor.execute("""
            INSERT INTO players (player_id, name, playing_role, batting_style, bowling_style, team_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name=VALUES(name),
                playing_role=VALUES(playing_role),
                batting_style=VALUES(batting_style),
                bowling_style=VALUES(bowling_style),
                team_id=VALUES(team_id)
        """, (pid, name, role, batting, bowling, team_id))
        db.commit()
        print(f"✅ Loaded: {name} (ID: {pid})")

if __name__ == "__main__":
    load_trending_players()
    cursor.close()
    db.close()
