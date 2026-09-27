import streamlit as st
from src.dashboard import load_data
from src.metrics import player_summary, player_song_summary, comment_summary
from src.ui import award_card
from src.theme import apply_retro_theme

data = load_data()
apply_retro_theme()
st.title("Leaderboard & Community Awards")
if "submissions" not in data or "players" not in data:
    st.info("Run refresh_data.py first to create the processed tables.")
    st.stop()

leaderboard = player_summary(data["submissions"], data["players"])
st.subheader("Overall standings")
st.caption("The main league table, plus how each player got there.")
standings = leaderboard.rename(columns={"rank":"Position", "player_name":"Player", "total_points":"Total points", "submissions":"Songs submitted", "average_points":"Average points", "wins":"Wins", "podiums":"Podiums"})
st.dataframe(standings[["Position", "Player", "Total points", "Songs submitted", "Average points", "Wins", "Podiums"]], hide_index=True, use_container_width=True, column_config={"Position": st.column_config.NumberColumn(help="League position based on total points."), "Average points": st.column_config.NumberColumn(help="Total points divided by songs submitted.", format="%.1f"), "Wins": st.column_config.NumberColumn(help="How many songs finished first."), "Podiums": st.column_config.NumberColumn(help="How many songs finished in the top three.")})

st.subheader("Player record leaderboards")
st.caption("These turn the song records into player averages, so one wild song does not decide the whole table.")
player_records = player_song_summary(data["submissions"], data["votes"], data["players"])
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

comments = comment_summary(data.get("comments"), data["players"])
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
