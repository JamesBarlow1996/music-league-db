import streamlit as st
from src.dashboard import load_data
from src.metrics import relationships, voting_summary, kingmaker_summary, participating_players
from src.ui import award_card
from src.theme import apply_retro_theme

data = load_data()
apply_retro_theme()
st.title("Voting & Relationships")
if not {"submissions", "votes", "players"}.issubset(data):
    st.info("Run refresh_data.py first to create the processed tables.")
    st.stop()

players = participating_players(data["players"], data["submissions"])
names = players.set_index("player_id")["player_name"]
voting = voting_summary(data["votes"], players)
left, right = st.columns(2)
generous = voting.sort_values("average_points_given", ascending=False).iloc[0]
harsh = voting.sort_values("average_points_given").iloc[0]
award_card(left, "Most Generous", generous["player_name"], f'{generous["average_points_given"]:.2f} points per vote', "Gives the most points on average when they vote.")
award_card(right, "Harshest Critic", harsh["player_name"], f'{harsh["average_points_given"]:.2f} points per vote', "Gives the fewest points on average when they vote.")

st.subheader("How everyone votes")
st.caption("This only looks at songs each person actually voted on.")
vote_table = voting.rename(columns={"player_name":"Player", "votes_cast":"Votes cast", "average_points_given":"Average points", "positive_vote_rate":"Positive votes", "negative_vote_rate":"Downvotes"})
vote_table["Positive votes"] *= 100
vote_table["Downvotes"] *= 100
st.dataframe(vote_table[["Player", "Average points", "Votes cast", "Positive votes", "Downvotes"]].sort_values("Average points", ascending=False), hide_index=True, use_container_width=True, column_config={"Positive votes": st.column_config.NumberColumn(format="%.0f%%"), "Downvotes": st.column_config.NumberColumn(format="%.0f%%")})

support = relationships(data["submissions"], data["votes"], players)
support["Voter"] = support["voter_player_id"].map(names)
support["Recipient"] = support["recipient_player_id"].map(names)
selected = st.selectbox("See a player's biggest fan and nemesis", players["player_name"].tolist())
selected_id = players.loc[players["player_name"] == selected, "player_id"].iloc[0]
player_support = support.loc[support["recipient_player_id"] == selected_id]
if not player_support.empty:
    fan = player_support.sort_values(["normalized_support", "raw_points"], ascending=False).iloc[0]
    nemesis = player_support.sort_values(["normalized_support", "raw_points"]).iloc[0]
    fan_col, nemesis_col = st.columns(2)
    award_card(fan_col, "Biggest Fan", fan["Voter"], f'{fan["raw_points"]:+.0f} points given', f'That is {fan["normalized_support"]:.2f} points per chance to vote.')
    award_card(nemesis_col, "Nemesis", nemesis["Voter"], f'{nemesis["raw_points"]:+.0f} points given', f'That is {nemesis["normalized_support"]:.2f} points per chance to vote.')

st.subheader("All voting relationships")
st.caption("Average support includes songs someone could have voted for but skipped, so it stays fair across rounds.")
relationship_table = support.rename(columns={"normalized_support":"Average support", "raw_points":"Total points given", "opportunities":"Chances to vote"})
st.dataframe(relationship_table[["Voter", "Recipient", "Average support", "Total points given", "Chances to vote"]].sort_values("Average support", ascending=False), hide_index=True, use_container_width=True)

kingmakers = kingmaker_summary(data["submissions"], data["votes"], players)
st.subheader("Kingmaker / Queenmaker")
st.caption("Who most often gave positive points to the song that went on to win the round.")
kingmaker_table = kingmakers.rename(columns={"player_name":"Player", "winners_backed":"Winners backed", "eligible_rounds":"Rounds they could back", "kingmaker_rate":"Success rate"})
kingmaker_table["Success rate"] *= 100
st.dataframe(kingmaker_table[["Player", "Winners backed", "Rounds they could back", "Success rate"]].sort_values(["Winners backed", "Success rate"], ascending=False), hide_index=True, use_container_width=True, column_config={"Success rate": st.column_config.NumberColumn(format="%.0f%%")})
