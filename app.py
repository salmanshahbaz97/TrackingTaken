import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Tekken Scorecard", layout="wide")
st.title("🎮 Tekken Scorecard — Salman vs Abdullah")

DATA_FILE = "data.csv"

if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
    pd.DataFrame(columns=["date", "salman_score", "abdullah_score"]).to_csv(DATA_FILE, index=False)

df = pd.read_csv(DATA_FILE)

# =====================
# SIDEBAR — DATA ENTRY FORM
# =====================
st.sidebar.header("📝 Log a Session")

with st.sidebar.form("add_session", clear_on_submit=True):
    game_date = st.date_input("Date")
    salman_score = st.number_input("Salman's score", min_value=0, step=1)
    abdullah_score = st.number_input("Abdullah's score", min_value=0, step=1)
    submitted = st.form_submit_button("Save Session")

    if submitted:
        new_row = pd.DataFrame([{
            "date": str(game_date),
            "salman_score": int(salman_score),
            "abdullah_score": int(abdullah_score),
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("Saved!")

# Reload
df = pd.read_csv(DATA_FILE)

if len(df) == 0:
    st.info("No sessions logged yet. Use the form on the left to add your first session!")
    st.stop()

df["date"] = pd.to_datetime(df["date"])
df["winner"] = df.apply(
    lambda r: "Salman" if r["salman_score"] > r["abdullah_score"]
    else ("Abdullah" if r["abdullah_score"] > r["salman_score"] else "Draw"),
    axis=1,
)

# =====================
# BIG METRICS
# =====================
salman_wins = (df["winner"] == "Salman").sum()
abdullah_wins = (df["winner"] == "Abdullah").sum()
total_sessions = len(df)

m1, m2, m3 = st.columns(3)
m1.metric("Salman Wins", salman_wins)
m2.metric("Abdullah Wins", abdullah_wins)
m3.metric("Total Sessions", total_sessions)

# =====================
# SCORE TABLE
# =====================
st.subheader("All Sessions")
display = df.sort_values("date", ascending=False)[["date", "salman_score", "abdullah_score", "winner"]].copy()
display["date"] = display["date"].dt.strftime("%Y-%m-%d")
st.dataframe(display, use_container_width=True, hide_index=True)

# =====================
# CHARTS
# =====================
col1, col2 = st.columns(2)

with col1:
    st.subheader("Wins Comparison")
    wins_df = pd.DataFrame({"Player": ["Salman", "Abdullah"], "Wins": [salman_wins, abdullah_wins]})
    st.bar_chart(wins_df.set_index("Player"))

with col2:
    st.subheader("Scores Per Session")
    scores_chart = df.set_index("date")[["salman_score", "abdullah_score"]].rename(
        columns={"salman_score": "Salman", "abdullah_score": "Abdullah"}
    )
    st.line_chart(scores_chart)

# =====================
# CUMULATIVE WIN RATE
# =====================
st.subheader("Cumulative Win Rate Over Time")
df_sorted = df.sort_values("date").reset_index(drop=True)
df_sorted["salman_cumwins"] = (df_sorted["winner"] == "Salman").cumsum()
df_sorted["abdullah_cumwins"] = (df_sorted["winner"] == "Abdullah").cumsum()
df_sorted["games"] = range(1, len(df_sorted) + 1)
df_sorted["Salman %"] = (df_sorted["salman_cumwins"] / df_sorted["games"] * 100).round(1)
df_sorted["Abdullah %"] = (df_sorted["abdullah_cumwins"] / df_sorted["games"] * 100).round(1)
st.line_chart(df_sorted.set_index("date")[["Salman %", "Abdullah %"]])

# =====================
# TOTAL SCORE
# =====================
st.subheader("Total Rounds Won")
total_salman = df["salman_score"].sum()
total_abdullah = df["abdullah_score"].sum()
t1, t2 = st.columns(2)
t1.metric("Salman Total Rounds", int(total_salman))
t2.metric("Abdullah Total Rounds", int(total_abdullah))
