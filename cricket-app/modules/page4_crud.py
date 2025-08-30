import streamlit as st
import mysql.connector
import pandas as pd

# --- DB Connection ---
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456789",
        database="cricketdb"
    )

# --- Fetch all valid team IDs ---
def get_team_ids():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT team_id FROM teams")
    teams = cursor.fetchall()
    conn.close()
    return [row[0] for row in teams]

# --- CRUD FUNCTIONS ---
def create_player(player):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO players (player_id, name, playing_role, batting_style, bowling_style, team_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name=VALUES(name),
            playing_role=VALUES(playing_role),
            batting_style=VALUES(batting_style),
            bowling_style=VALUES(bowling_style),
            team_id=VALUES(team_id)
    """, player)
    conn.commit()
    conn.close()

def read_players():
    conn = get_connection()
    df = pd.read_sql("SELECT player_id, name, playing_role, batting_style, bowling_style, team_id FROM players", conn)
    conn.close()
    return df

def update_player(player_id, updates):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE players 
        SET name=%s, playing_role=%s, batting_style=%s, bowling_style=%s, team_id=%s
        WHERE player_id=%s
    """, (*updates, player_id))
    conn.commit()
    conn.close()

def delete_player(player_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM players WHERE player_id=%s", (player_id,))
    conn.commit()
    conn.close()

# --- STREAMLIT PAGE ---
def run():
    st.title("⚡ Player Management (CRUD)")

    team_ids = get_team_ids()
    if not team_ids:
        st.error("No valid teams found in the database. Please add teams first.")
        return

    option = st.selectbox("Choose operation", ["Create", "Read", "Update", "Delete"])

    # CREATE
    if option == "Create":
        st.subheader("➕ Add Player")
        player_id = st.number_input("Player ID", min_value=1, step=1)
        name = st.text_input("Name")
        playing_role = st.text_input("Playing Role")
        batting_style = st.text_input("Batting Style")
        bowling_style = st.text_input("Bowling Style")
        team_id = st.selectbox("Team ID", team_ids)

        if st.button("Add Player"):
            create_player((player_id, name, playing_role, batting_style, bowling_style, team_id))
            st.success(f"✅ Player {name} added successfully!")

    # READ
    elif option == "Read":
        st.subheader("📖 Player List")
        df = read_players()
        st.dataframe(df, use_container_width=True)

    # UPDATE
    elif option == "Update":
        st.subheader("✏️ Update Player")
        df = read_players()
        if not df.empty:
            player_id = st.selectbox("Select Player ID", df["player_id"].tolist())
            player_row = df[df["player_id"] == player_id].iloc[0]

            name = st.text_input("Name", player_row["name"])
            playing_role = st.text_input("Playing Role", player_row["playing_role"])
            batting_style = st.text_input("Batting Style", player_row["batting_style"])
            bowling_style = st.text_input("Bowling Style", player_row["bowling_style"])
            team_id = st.selectbox("Team ID", team_ids, index=team_ids.index(player_row["team_id"]) if player_row["team_id"] in team_ids else 0)

            if st.button("Update Player"):
                update_player(player_id, (name, playing_role, batting_style, bowling_style, team_id))
                st.success(f"✅ Player {name} updated successfully!")

    # DELETE
    elif option == "Delete":
        st.subheader("🗑️ Delete Player")
        df = read_players()
        if not df.empty:
            player_id = st.selectbox("Select Player ID", df["player_id"].tolist())
            if st.button("Delete Player"):
                delete_player(player_id)
                st.success(f"✅ Player {player_id} deleted successfully!")

if __name__ == "__main__":
    run()
