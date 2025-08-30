import streamlit as st
import mysql.connector
import pandas as pd

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456789",
        database="cricketdb"
    )

QUERIES = {
    # ---------- Beginner Level ----------
    "Q1. Find all players who represent India": """
        SELECT p.name AS player_name, p.playing_role, p.batting_style, p.bowling_style
        FROM players p
        JOIN teams t ON p.team_id = t.team_id
        WHERE t.country = 'India';
    """,
    "Q2. Matches in last 30 days": """
        SELECT m.match_desc, t1.team_name AS team1, t2.team_name AS team2,
               v.ground AS venue, v.city, m.start_date
        FROM matches m
        JOIN venues v ON m.venue_id = v.venue_id
        JOIN teams t1 ON m.team1_id = t1.team_id
        JOIN teams t2 ON m.team2_id = t2.team_id
        WHERE m.start_date >= NOW() - INTERVAL 30 DAY
        ORDER BY m.start_date DESC;
    """,
    "Q3. Top 10 highest ODI run scorers": """
        -- 🚧 Needs batting_stats table
        SELECT player_id, total_runs, batting_avg, centuries
        FROM batting_stats
        WHERE format = 'ODI'
        ORDER BY total_runs DESC
        LIMIT 10;
    """,
    "Q4. Venues with capacity > 50,000": """
        SELECT ground, city, country, capacity
        FROM venues
        WHERE capacity > 50000
        ORDER BY capacity DESC;
    """,
    "Q5. Matches won by each team": """
        SELECT t.team_name, COUNT(*) AS total_wins
        FROM matches m
        JOIN teams t ON m.winner_id = t.team_id
        GROUP BY t.team_name
        ORDER BY total_wins DESC;
    """,
    "Q6. Count of players by role": """
        SELECT playing_role, COUNT(*) AS total_players
        FROM players
        GROUP BY playing_role
        ORDER BY total_players DESC;
    """,
    "Q7. Highest score by format": """
        -- 🚧 Needs batting_scores table with format info
        SELECT format, MAX(runs) AS highest_score
        FROM batting_scores
        GROUP BY format;
    """,
    "Q8. Series that started in 2024": """
        SELECT name AS series_name, host_country, match_type, start_date, total_matches
        FROM series
        WHERE YEAR(start_date) = 2024;
    """,

    # ---------- Intermediate Level ----------
    "Q9. All-rounders with 1000+ runs & 50+ wickets": """
        -- 🚧 Needs career_stats table
        SELECT player_id, format, runs, wickets
        FROM career_stats
        WHERE runs > 1000 AND wickets > 50 AND playing_role = 'All-rounder';
    """,
    "Q10. Last 20 completed matches": """
        SELECT m.match_desc, t1.team_name, t2.team_name, tw.team_name AS winner,
               m.result_margin, m.result_type, v.ground
        FROM matches m
        JOIN teams t1 ON m.team1_id = t1.team_id
        JOIN teams t2 ON m.team2_id = t2.team_id
        LEFT JOIN teams tw ON m.winner_id = tw.team_id
        JOIN venues v ON m.venue_id = v.venue_id
        WHERE m.winner_id IS NOT NULL
        ORDER BY m.start_date DESC
        LIMIT 20;
    """,
    "Q11. Player performance across formats": """
        -- 🚧 Needs batting_stats table with format dimension
        SELECT player_id,
               SUM(CASE WHEN format='Test' THEN runs ELSE 0 END) AS test_runs,
               SUM(CASE WHEN format='ODI' THEN runs ELSE 0 END) AS odi_runs,
               SUM(CASE WHEN format='T20I' THEN runs ELSE 0 END) AS t20_runs,
               AVG(batting_avg) AS overall_batting_avg
        FROM batting_stats
        GROUP BY player_id
        HAVING COUNT(DISTINCT format) >= 2;
    """,
    "Q12. Team performance home vs away": """
        SELECT t.team_name,
               SUM(CASE WHEN v.country = t.country AND m.winner_id = t.team_id THEN 1 ELSE 0 END) AS home_wins,
               SUM(CASE WHEN v.country != t.country AND m.winner_id = t.team_id THEN 1 ELSE 0 END) AS away_wins
        FROM matches m
        JOIN venues v ON m.venue_id = v.venue_id
        JOIN teams t ON (m.team1_id = t.team_id OR m.team2_id = t.team_id)
        GROUP BY t.team_name;
    """,
    "Q13. 100+ partnerships": """
        -- 🚧 Needs partnerships table
        SELECT bat1_id, bat2_id, total_runs, innings_id
        FROM partnerships
        WHERE total_runs >= 100;
    """,
    "Q14. Bowling performance by venue": """
        -- 🚧 Needs bowling_figures table
        SELECT bowler_id, venue_id, AVG(economy) AS avg_economy,
               SUM(wickets) AS total_wickets, COUNT(match_id) AS matches_played
        FROM bowling_figures
        GROUP BY bowler_id, venue_id
        HAVING COUNT(match_id) >= 3;
    """,
    "Q15. Players in close matches": """
        -- 🚧 Needs batting_scores + match margin
        SELECT player_id, AVG(runs) AS avg_runs, COUNT(*) AS close_matches,
               SUM(CASE WHEN team_id = winner_id THEN 1 ELSE 0 END) AS wins_in_close
        FROM batting_scores b
        JOIN matches m ON b.match_id = m.match_id
        WHERE (m.result_type = 'runs' AND m.result_margin < 50)
           OR (m.result_type = 'wickets' AND m.result_margin < 5)
        GROUP BY player_id;
    """,
    "Q16. Batting performance trend since 2020": """
        -- 🚧 Needs batting_scores table with strike_rate
        SELECT player_id, YEAR(m.start_date) AS year,
               AVG(runs) AS avg_runs, AVG(strike_rate) AS avg_sr
        FROM batting_scores b
        JOIN matches m ON b.match_id = m.match_id
        WHERE YEAR(m.start_date) >= 2020
        GROUP BY player_id, YEAR(m.start_date)
        HAVING COUNT(match_id) >= 5;
    """,

    # ---------- Advanced Level ----------
    "Q17. Toss advantage analysis": """
        -- 🚧 Needs toss info in matches table
        SELECT
            SUM(CASE WHEN m.toss_winner_id = m.winner_id THEN 1 ELSE 0 END) / COUNT(*) * 100 AS toss_advantage_pct,
            m.toss_decision
        FROM matches m
        WHERE m.toss_winner_id IS NOT NULL AND m.winner_id IS NOT NULL
        GROUP BY m.toss_decision;
    """,
    "Q18. Economical bowlers in ODIs/T20s": """
        -- 🚧 Needs bowling_figures table
        SELECT bowler_id,
               AVG(economy) AS avg_economy,
               SUM(wickets) AS total_wickets,
               COUNT(match_id) AS matches_played
        FROM bowling_figures
        WHERE format IN ('ODI', 'T20')
        GROUP BY bowler_id
        HAVING COUNT(match_id) >= 10 AND AVG(overs) >= 2
        ORDER BY avg_economy ASC, total_wickets DESC;
    """,
    "Q19. Consistent batsmen analysis": """
        -- 🚧 Needs ball-by-ball or innings-level batting data
        SELECT player_id,
               AVG(runs) AS avg_runs,
               STDDEV(runs) AS runs_stddev
        FROM batting_scores
        WHERE balls_faced >= 10 AND YEAR(match_date) >= 2022
        GROUP BY player_id
        HAVING COUNT(match_id) >= 5
        ORDER BY runs_stddev ASC;
    """,
    "Q20. Matches by player & format averages": """
        -- 🚧 Needs player_format_stats table
        SELECT player_id, format, COUNT(match_id) AS matches_played, AVG(batting_avg) AS avg_batting
        FROM player_format_stats
        GROUP BY player_id, format
        HAVING SUM(matches_played) >= 20;
    """,
    "Q21. Performance ranking system": """
        -- 🚧 Needs combined batting/bowling/fielding stats
        SELECT player_id,
           ((runs_scored * 0.01) + (batting_average * 0.5) + (strike_rate * 0.3) + (wickets_taken * 2)
           + ((50 - bowling_average) * 0.5) + ((6 - economy_rate) * 2) + (catches * 1) + (stumpings * 1)) AS performance_score,
           format
        FROM player_performance_stats
        WHERE format IN ('Test', 'ODI', 'T20')
        ORDER BY performance_score DESC;
    """,
    "Q22. Head-to-head analysis": """
        -- 🚧 Needs matches table with proper historical data
        SELECT t1.team_name AS team1, t2.team_name AS team2,
            COUNT(*) AS total_played,
            SUM(CASE WHEN m.winner_id = t1.team_id THEN 1 ELSE 0 END) AS team1_wins,
            SUM(CASE WHEN m.winner_id = t2.team_id THEN 1 ELSE 0 END) AS team2_wins
        FROM matches m
        JOIN teams t1 ON m.team1_id = t1.team_id
        JOIN teams t2 ON m.team2_id = t2.team_id
        WHERE m.start_date >= NOW() - INTERVAL 3 YEAR
        GROUP BY team1, team2
        HAVING COUNT(*) >= 5;
    """,
    "Q23. Recent form analysis": """
        -- 🚧 Needs per-match batting records
        SELECT player_id,
               AVG(CASE WHEN match_num <= 5 THEN runs ELSE NULL END) AS last5_avg,
               AVG(CASE WHEN match_num <= 10 THEN runs ELSE NULL END) AS last10_avg,
               SUM(CASE WHEN runs >= 50 THEN 1 ELSE 0 END) AS scores_50plus,
               STDDEV(runs) AS consistency_score
        FROM player_recent_form
        GROUP BY player_id;
    """,
    "Q24. Batting partnerships success": """
        -- 🚧 Needs partnerships table
        SELECT bat1_id, bat2_id,
               AVG(total_runs) AS avg_partnership,
               SUM(CASE WHEN total_runs > 50 THEN 1 ELSE 0 END) AS good_partnerships,
               MAX(total_runs) AS highest_partnership,
               COUNT(*) AS total_partnerships
        FROM partnerships
        WHERE ABS(bat1_id - bat2_id) = 1
        GROUP BY bat1_id, bat2_id
        HAVING COUNT(*) >= 5
        ORDER BY avg_partnership DESC;
    """,
    "Q25. Time-series career evolution": """
        -- 🚧 Needs quarterly aggregation of batting_scores
        SELECT player_id, 
               CONCAT(YEAR(match_date), '-', QUARTER(match_date)) AS period,
               AVG(runs) AS avg_runs, AVG(strike_rate) AS avg_sr
        FROM batting_scores
        GROUP BY player_id, period
        ORDER BY player_id, period;
    """
}

def run_query(sql):
    conn = get_connection()
    try:
        df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        st.error(f"Error running query: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def run():
    st.title("🏏 Cricket SQL Analysis (25 Questions)")
    level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"])
    level_map = {
        "Beginner": [k for k in QUERIES if k.startswith("Q") and int(k.split(".")[0][1:]) <= 8],
        "Intermediate": [k for k in QUERIES if k.startswith("Q") and 9 <= int(k.split(".")[0][1:]) <= 16],
        "Advanced": [k for k in QUERIES if k.startswith("Q") and 17 <= int(k.split(".")[0][1:]) <= 25]
    }
    question = st.selectbox("Select a query", level_map[level])
    if st.button("Run Query"):
        sql = QUERIES[question]
        if sql.strip().startswith("-- 🚧"):
            st.warning("This query requires additional stats tables not yet in your schema.")
        else:
            df = run_query(sql)
            if df.empty:
                st.info("No results found for this query. Please check that your tables have sufficient data.")
            else:
                st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    run()
