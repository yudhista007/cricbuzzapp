# db_update_stats.py
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

# --- API Credentials ---
API_KEY = "3883e581ecmshcef93fbe41a5e04p1b0b4ejsn9b557e3dfd67"
API_HOST = "cricbuzz-cricket.p.rapidapi.com"

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST
}

# ---------------- Batting Stats Loader ----------------
def load_batting_stats(player_id: int):
    url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}/batting"
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        print(f"❌ Failed to fetch batting stats for player {player_id}")
        return

    data = resp.json().get("stats", [])
    for stat in data:
        fmt = stat.get("format", "")
        matches = stat.get("matches", 0)
        innings = stat.get("innings", 0)
        runs = stat.get("runs", 0)
        balls = stat.get("balls", 0)
        highest = stat.get("highest", "")
        average = stat.get("average", 0.0)
        strike_rate = stat.get("strikeRate", 0.0)
        not_outs = stat.get("notOuts", 0)
        fours = stat.get("fours", 0)
        sixes = stat.get("sixes", 0)
        ducks = stat.get("ducks", 0)
        fifties = stat.get("fifties", 0)
        hundreds = stat.get("hundreds", 0)
        double_hundreds = stat.get("doubleHundreds", 0)
        triple_hundreds = stat.get("tripleHundreds", 0)
        quadruple_hundreds = stat.get("quadrupleHundreds", 0)

        cursor.execute("""
            INSERT INTO batting_stats
            (player_id, format, matches, innings, runs, balls, highest, average, strike_rate, not_outs,
             fours, sixes, ducks, fifties, hundreds, double_hundreds, triple_hundreds, quadruple_hundreds)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            player_id, fmt, matches, innings, runs, balls, highest, average, strike_rate, not_outs,
            fours, sixes, ducks, fifties, hundreds, double_hundreds, triple_hundreds, quadruple_hundreds
        ))

    db.commit()
    print(f"✅ Batting stats inserted for player {player_id}")


# ---------------- Bowling Stats Loader ----------------
def load_bowling_stats(player_id: int):
    url = f"https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/{player_id}/bowling"
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        print(f"❌ Failed to fetch bowling stats for player {player_id}")
        return

    data = resp.json().get("stats", [])
    for stat in data:
        fmt = stat.get("format", "")
        matches = stat.get("matches", 0)
        innings = stat.get("innings", 0)
        balls = stat.get("balls", 0)
        runs = stat.get("runs", 0)
        maidens = stat.get("maidens", 0)
        wickets = stat.get("wickets", 0)
        average = stat.get("average", 0.0)
        economy = stat.get("economy", 0.0)
        strike_rate = stat.get("strikeRate", 0.0)
        bbi = stat.get("bbi", "")
        bbm = stat.get("bbm", "")
        four_wkts = stat.get("fourWickets", 0)
        five_wkts = stat.get("fiveWickets", 0)
        ten_wkts = stat.get("tenWickets", 0)

        cursor.execute("""
            INSERT INTO bowling_stats
            (player_id, format, matches, innings, balls, runs, maidens, wickets,
             average, economy, strike_rate, bbi, bbm, four_wickets, five_wickets, ten_wickets)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            player_id, fmt, matches, innings, balls, runs, maidens, wickets,
            average, economy, strike_rate, bbi, bbm, four_wkts, five_wkts, ten_wkts
        ))

    db.commit()
    print(f"✅ Bowling stats inserted for player {player_id}")


# ---------------- Main ----------------
if __name__ == "__main__":
    player_id = 8733   # example: Virat Kohli
    load_batting_stats(player_id)
    load_bowling_stats(player_id)

    cursor.close()
    db.close()
    print("🎉 Stats updated successfully")
