import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Tekken Scorecard", layout="wide")

DATA_FILE = "data.csv"

if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
    pd.DataFrame(columns=["date", "salman_score", "abdullah_score"]).to_csv(DATA_FILE, index=False)


def load_data():
    df = pd.read_csv(DATA_FILE)
    if len(df) > 0:
        df["date"] = pd.to_datetime(df["date"])
        df["winner"] = df.apply(
            lambda r: "Salman" if r["salman_score"] > r["abdullah_score"]
            else ("Abdullah" if r["abdullah_score"] > r["salman_score"] else "Draw"),
            axis=1,
        )
        df["score_diff"] = (df["salman_score"] - df["abdullah_score"]).abs()
    return df


# =====================
# AUTHENTICATION
# =====================
def check_password():
    """Gate data-entry behind a password stored in Streamlit secrets or fallback."""
    correct_pw = st.secrets.get("password", "tekken2026") if hasattr(st, "secrets") else "tekken2026"

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    with st.sidebar.form("login_form"):
        st.subheader("🔒 Admin Login")
        pw = st.text_input("Password", type="password")
        login = st.form_submit_button("Login")
        if login:
            if pw == correct_pw:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Wrong password!")
    return False


is_admin = check_password()

# =====================
# SIDEBAR — DATA ENTRY (ADMIN ONLY)
# =====================
df = load_data()

if is_admin:
    st.sidebar.divider()
    st.sidebar.header("📝 Log a Session")
    with st.sidebar.form("add_session", clear_on_submit=True):
        game_date = st.date_input("Date")
        salman_score = st.number_input("Salman's score", min_value=0, step=1)
        abdullah_score = st.number_input("Abdullah's score", min_value=0, step=1)
        submitted = st.form_submit_button("💾 Save Session")
        if submitted:
            new_row = pd.DataFrame([{
                "date": str(game_date),
                "salman_score": int(salman_score),
                "abdullah_score": int(abdullah_score),
            }])
            full = pd.read_csv(DATA_FILE)
            full = pd.concat([full, new_row], ignore_index=True)
            full.to_csv(DATA_FILE, index=False)
            st.rerun()

    # Delete session
    if len(df) > 0:
        st.sidebar.divider()
        st.sidebar.header("🗑️ Delete a Session")
        labels = [
            f"#{i+1} — {r['date'].strftime('%Y-%m-%d')} | {int(r['salman_score'])}-{int(r['abdullah_score'])}"
            for i, r in df.iterrows()
        ]
        to_delete = st.sidebar.selectbox("Select session", labels)
        if st.sidebar.button("Delete Selected"):
            idx = labels.index(to_delete)
            full = pd.read_csv(DATA_FILE)
            full = full.drop(index=idx).reset_index(drop=True)
            full.to_csv(DATA_FILE, index=False)
            st.rerun()

    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.rerun()

# =====================
# MAIN AREA
# =====================
st.title("🎮 Tekken Scorecard — Salman vs Abdullah")

df = load_data()

if len(df) == 0:
    st.info("No sessions logged yet.")
    st.stop()

# =====================
# FILTERS
# =====================
with st.expander("🔍 Filters", expanded=False):
    fc1, fc2 = st.columns(2)
    with fc1:
        min_date = df["date"].min().date()
        max_date = df["date"].max().date()
        date_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    with fc2:
        winner_filter = st.multiselect("Filter by winner", ["Salman", "Abdullah", "Draw"], default=["Salman", "Abdullah", "Draw"])

    if isinstance(date_range, tuple) and len(date_range) == 2:
        df = df[(df["date"].dt.date >= date_range[0]) & (df["date"].dt.date <= date_range[1])]
    df = df[df["winner"].isin(winner_filter)]

if len(df) == 0:
    st.warning("No sessions match your filters.")
    st.stop()

salman_wins = (df["winner"] == "Salman").sum()
abdullah_wins = (df["winner"] == "Abdullah").sum()
total_sessions = len(df)

# =====================
# TABS
# =====================
tab_overview, tab_h2h, tab_trends, tab_records = st.tabs(
    ["📊 Overview", "⚔️ Head to Head", "📈 Trends", "🏆 Records"]
)

# =====================
# TAB: OVERVIEW
# =====================
with tab_overview:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Salman Wins", salman_wins)
    m2.metric("Abdullah Wins", abdullah_wins)
    m3.metric("Total Sessions", total_sessions)
    leader = "Salman" if salman_wins > abdullah_wins else ("Abdullah" if abdullah_wins > salman_wins else "Tied!")
    m4.metric("Current Leader", leader)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Wins Comparison")
        wins_df = pd.DataFrame({"Player": ["Salman", "Abdullah"], "Wins": [salman_wins, abdullah_wins]})
        st.bar_chart(wins_df.set_index("Player"))

    with col2:
        st.subheader("Win Distribution")
        pie_data = pd.DataFrame({
            "Result": ["Salman", "Abdullah", "Draw"],
            "Count": [salman_wins, abdullah_wins, (df["winner"] == "Draw").sum()]
        })
        pie_data = pie_data[pie_data["Count"] > 0]
        st.bar_chart(pie_data.set_index("Result"))

    st.subheader("Total Rounds Won")
    total_salman = int(df["salman_score"].sum())
    total_abdullah = int(df["abdullah_score"].sum())
    t1, t2, t3 = st.columns(3)
    t1.metric("Salman Rounds", total_salman)
    t2.metric("Abdullah Rounds", total_abdullah)
    t3.metric("Round Leader", "Salman" if total_salman > total_abdullah else "Abdullah")

# =====================
# TAB: HEAD TO HEAD
# =====================
with tab_h2h:
    st.subheader("⚔️ Session-by-Session Breakdown")
    df_sorted = df.sort_values("date").reset_index(drop=True)

    for _, row in df_sorted.iterrows():
        date_str = row["date"].strftime("%Y-%m-%d")
        s = int(row["salman_score"])
        a = int(row["abdullah_score"])
        w = row["winner"]
        emoji = "🔵" if w == "Salman" else ("🔴" if w == "Abdullah" else "⚪")
        diff = int(row["score_diff"])

        c1, c2, c3, c4, c5 = st.columns([2, 1.5, 0.5, 1.5, 2])
        c1.write(f"**{date_str}**")
        c2.write(f"Salman: **{s}**")
        c3.write(f"{emoji}")
        c4.write(f"Abdullah: **{a}**")
        c5.write(f"{w} by {diff}" if w != "Draw" else "Draw")

    st.divider()
    st.subheader("🔥 Streaks")
    winners = df_sorted["winner"].tolist()

    def calc_streaks(winners_list, player):
        current = 0
        best = 0
        for w in winners_list:
            if w == player:
                current += 1
                best = max(best, current)
            else:
                current = 0
        return current, best

    s_cur, s_best = calc_streaks(winners, "Salman")
    a_cur, a_best = calc_streaks(winners, "Abdullah")

    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Salman Current Streak", f"{s_cur} 🔥" if s_cur > 0 else "0")
    sc2.metric("Salman Best Streak", s_best)
    sc3.metric("Abdullah Current Streak", f"{a_cur} 🔥" if a_cur > 0 else "0")
    sc4.metric("Abdullah Best Streak", a_best)

# =====================
# TAB: TRENDS
# =====================
with tab_trends:
    st.subheader("Scores Per Session")
    scores_chart = df.sort_values("date").set_index("date")[["salman_score", "abdullah_score"]].rename(
        columns={"salman_score": "Salman", "abdullah_score": "Abdullah"}
    )
    st.line_chart(scores_chart)

    st.subheader("Cumulative Win Rate Over Time")
    df_trend = df.sort_values("date").reset_index(drop=True)
    df_trend["salman_cumwins"] = (df_trend["winner"] == "Salman").cumsum()
    df_trend["abdullah_cumwins"] = (df_trend["winner"] == "Abdullah").cumsum()
    df_trend["games"] = range(1, len(df_trend) + 1)
    df_trend["Salman %"] = (df_trend["salman_cumwins"] / df_trend["games"] * 100).round(1)
    df_trend["Abdullah %"] = (df_trend["abdullah_cumwins"] / df_trend["games"] * 100).round(1)
    st.line_chart(df_trend.set_index("date")[["Salman %", "Abdullah %"]])

    st.subheader("Score Margin Over Time")
    df_margin = df.sort_values("date").copy()
    df_margin["Salman Margin"] = df_margin["salman_score"] - df_margin["abdullah_score"]
    st.bar_chart(df_margin.set_index("date")["Salman Margin"])
    st.caption("Positive = Salman dominated, Negative = Abdullah dominated")

# =====================
# TAB: RECORDS
# =====================
with tab_records:
    st.subheader("🏆 Records & Fun Stats")

    r1, r2 = st.columns(2)
    with r1:
        best_salman = df.loc[df["salman_score"].idxmax()]
        st.metric("Salman's Best Score", int(best_salman["salman_score"]),
                  delta=f"on {best_salman['date'].strftime('%Y-%m-%d')}")
        st.metric("Salman Avg Score", f"{df['salman_score'].mean():.1f}")

        closest = df.loc[df["score_diff"].idxmin()]
        st.metric("Closest Game", f"{int(closest['salman_score'])}-{int(closest['abdullah_score'])}",
                  delta=f"on {closest['date'].strftime('%Y-%m-%d')}")

    with r2:
        best_abdullah = df.loc[df["abdullah_score"].idxmax()]
        st.metric("Abdullah's Best Score", int(best_abdullah["abdullah_score"]),
                  delta=f"on {best_abdullah['date'].strftime('%Y-%m-%d')}")
        st.metric("Abdullah Avg Score", f"{df['abdullah_score'].mean():.1f}")

        biggest = df.loc[df["score_diff"].idxmax()]
        st.metric("Biggest Blowout", f"{int(biggest['salman_score'])}-{int(biggest['abdullah_score'])}",
                  delta=f"{biggest['winner']} by {int(biggest['score_diff'])}")

    st.divider()
    total_rounds = int(df["salman_score"].sum() + df["abdullah_score"].sum())
    st.metric("🎮 Total Rounds Played Together", total_rounds)
