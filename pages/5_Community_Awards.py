import streamlit as st
import plotly.express as px
from src.dashboard import load_data
from src.metrics import player_summary, player_song_summary, comment_summary, participating_players
from src.ui import award_card
from src.theme import apply_retro_theme

data = load_data()
apply_retro_theme()
st.title("Leaderboard & Community Awards")
if "submissions" not in data or "players" not in data:
    st.info("Run refresh_data.py first to create the processed tables.")
    st.stop()

award_players = participating_players(data["players"], data["submissions"])
leaderboard = player_summary(data["submissions"], award_players)
st.subheader("Overall standings")
st.caption("The main league table, plus how each player got there.")
standings = leaderboard.rename(columns={"rank":"Position", "player_name":"Player", "total_points":"Total points", "submissions":"Songs submitted", "average_points":"Average points", "wins":"Wins", "podiums":"Podiums"})
st.dataframe(standings[["Position", "Player", "Total points", "Songs submitted", "Average points", "Wins", "Podiums"]], hide_index=True, use_container_width=True, column_config={"Position": st.column_config.NumberColumn(help="League position based on total points."), "Average points": st.column_config.NumberColumn(help="Total points divided by songs submitted.", format="%.1f"), "Wins": st.column_config.NumberColumn(help="How many songs finished first."), "Podiums": st.column_config.NumberColumn(help="How many songs finished in the top three.")})

st.subheader("Cumulative points over time")
st.caption("Each line shows how a player's total score has built up round by round. Curves are smoothed visually; markers show the actual round totals.")
rounds = data.get("rounds")
if rounds is not None and {"round_id", "round_name", "round_number"}.issubset(rounds.columns):
    round_axis = rounds[["round_id", "round_name", "round_number"]].drop_duplicates("round_id").sort_values("round_number")
else:
    round_axis = data["submissions"][["round_id"]].drop_duplicates().sort_values("round_id")
    round_axis["round_name"] = round_axis["round_id"]
    round_axis["round_number"] = range(1, len(round_axis) + 1)

players_axis = award_players[["player_id", "player_name"]].drop_duplicates()
progression = round_axis.merge(players_axis, how="cross")
round_points = data["submissions"].groupby(["round_id", "player_id"], as_index=False)["total_points"].sum()
progression = progression.merge(round_points, on=["round_id", "player_id"], how="left")
progression["total_points"] = progression["total_points"].fillna(0)
progression = progression.sort_values(["player_id", "round_number"])
progression["cumulative_points"] = progression.groupby("player_id")["total_points"].cumsum()
progression = progression.sort_values("round_number")
progression["chart_player_name"] = progression["player_name"].str.replace(r"^\s*\d+\s*", "", regex=True)

progression_chart = px.line(
    progression,
    x="round_name",
    y="cumulative_points",
    color="chart_player_name",
    markers=True,
    custom_data=["total_points"],
    labels={"round_name": "Round", "cumulative_points": "Cumulative points", "chart_player_name": "Player", "total_points": "Round points"},
)
progression_chart.update_traces(
    line={"shape": "spline", "smoothing": 1.1},
    hovertemplate="%{fullData.name}<br>%{x}<br>Cumulative points: %{y}<br>Round points: %{customdata[0]}<extra></extra>",
)
progression_chart.update_layout(hovermode="x unified", legend_title_text="Player")
st.plotly_chart(progression_chart, use_container_width=True)

st.subheader("Player record leaderboards")
st.caption("These turn the song records into player averages, so one wild song does not decide the whole table.")
player_records = player_song_summary(data["submissions"], data["votes"], award_players)
record_names = player_records.rename(columns={"rank":"Overall position", "player_name":"Player", "total_points":"Total points", "average_points":"Average points", "wins":"Wins", "podiums":"Podiums", "average_engagement":"Average engagement", "average_marmite":"Average Marmite spread"})
tab_overall, tab_engagement, tab_marmite = st.tabs(["Overall", "Engagement", "Marmite"])
with tab_overall:
    st.dataframe(record_names[["Overall position", "Player", "Total points", "Average points", "Wins", "Podiums"]].sort_values("Overall position"), hide_index=True, use_container_width=True)
with tab_engagement:
    engagement = record_names[["Player", "Average engagement"]].sort_values("Average engagement", ascending=False).copy()
    engagement["Average engagement"] *= 100
    st.caption("Average share of eligible voters who voted on each player's songs.")
    st.dataframe(engagement, hide_index=True, use_container_width=True, column_config={"Average engagement": st.column_config.NumberColumn(format="%.0f%%")})
with tab_marmite:
    st.caption("Average gap between the highest and lowest votes on each player's songs. Downvotes count.")
    st.dataframe(record_names[["Player", "Average Marmite spread"]].sort_values("Average Marmite spread", ascending=False), hide_index=True, use_container_width=True)

comments = comment_summary(data.get("comments"), award_players)
most_vocal = comments.sort_values("total_words", ascending=False).iloc[0]
mute = comments.sort_values(["total_words", "comment_count"]).iloc[0]
regulars = comments.loc[comments["comment_count"] >= 3]
if regulars.empty:
    regulars = comments.loc[comments["comment_count"] > 0]
essayist = regulars.sort_values("average_words", ascending=False).iloc[0] if not regulars.empty else None
drive_by = regulars.sort_values("average_words").iloc[0] if not regulars.empty else None
starter = comments.sort_values("submissions_commented_on", ascending=False).iloc[0]

st.subheader("Comment awards")
row_one = st.columns(2)
award_card(row_one[0], "Most Vocal", most_vocal["player_name"], f'{most_vocal["total_words"]:.0f} words', "Wrote the most across submission notes and vote comments.")
award_card(row_one[1], "The Mute", mute["player_name"], f'{mute["total_words"]:.0f} words', "Wrote the least. Zero-word players count too.")
row_one = st.columns(2)
award_card(row_one[0], "Conversation Starter", starter["player_name"], f'{starter["submissions_commented_on"]:.0f} songs commented on', "Left comments on the widest mix of other songs.")
if essayist is not None and drive_by is not None:
    award_card(row_one[1], "Essayist", essayist["player_name"], f'{essayist["average_words"]:.1f} words per comment', "Writes the longest comments on average, among regular commenters.")
    row_two = st.columns(2)
    award_card(row_two[0], "Drive-By Critic", drive_by["player_name"], f'{drive_by["average_words"]:.1f} words per comment', "Keeps comments shortest, among regular commenters.")

st.subheader("Everyone's comment stats")
st.caption("Submission notes and voting comments are both included, except Conversation Starter only counts voting comments.")
comment_table = comments.rename(columns={"player_name":"Player", "comment_count":"Comments", "total_words":"Words written", "average_words":"Words per comment", "submissions_commented_on":"Different songs commented on"})
st.dataframe(comment_table[["Player", "Comments", "Words written", "Words per comment", "Different songs commented on"]].sort_values("Words written", ascending=False), hide_index=True, use_container_width=True)
