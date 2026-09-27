import streamlit as st
from src.dashboard import load_data
from src.metrics import song_metrics
from src.theme import apply_retro_theme

data = load_data()
apply_retro_theme()
st.title("Songs & Records")
if "submissions" not in data or "votes" not in data or "players" not in data:
    st.info("Run refresh_data.py first to create the processed tables.")
    st.stop()

songs = song_metrics(data["submissions"], data["votes"], data["players"])
enrichment = data.get("track_enrichment")
if enrichment is not None:
    songs = songs.merge(enrichment[["spotify_track_id", "spotify_uri", "duration_ms", "popularity_score"]], on=["spotify_track_id", "spotify_uri"], how="left")
names = data["players"][["player_id", "player_name"]]
rounds = data.get("rounds", data["submissions"][["round_id"]].drop_duplicates())
if "round_name" not in rounds.columns:
    rounds = rounds.assign(round_name=rounds["round_id"])
display = songs.merge(names, on="player_id", how="left").merge(rounds[["round_id", "round_name"]], on="round_id", how="left")
if "duration_ms" not in display.columns:
    display["duration_ms"] = None
display["Duration"] = display["duration_ms"].fillna(0).map(lambda value: f"{int(value // 60000)}:{int((value % 60000) // 1000):02d}" if value else "—")
display = display.rename(columns={"track_name":"Track", "artist_display":"Artist", "player_name":"Submitted by", "round_name":"Round", "total_points":"Points", "engagement_rate":"Engagement rate", "marmite_spread":"Marmite spread", "voter_comment_count":"Voter comments", "voter_comment_words":"Comment words", "avg_explicit_vote":"Average vote", "vote_min":"Lowest vote", "vote_max":"Highest vote", "explicit_voters":"People who voted", "eligible_voters":"People who could vote", "crowd_pleaser_score":"Crowd pleaser score", "cult_classic_score":"Cult classic score", "consensus_score":"Vote disagreement"})
COLUMN_HELP = {
    "Track": "Submitted track title.",
    "Artist": "Artist or artists shown in the Music League export.",
    "Submitted by": "Player who submitted the song.",
    "Round": "Music League round containing the submission.",
    "Points": "Signed sum of explicit votes for the song.",
    "Engagement rate": "Explicit voters divided by eligible voters.",
    "Marmite spread": "Highest vote minus lowest vote, including downvotes.",
    "Lowest vote": "Lowest vote the song received, including downvotes.",
    "Highest vote": "Highest vote the song received.",
    "People who voted": "How many people cast any vote on the song.",
    "People who could vote": "Everyone in the round apart from the submitter.",
    "Voter comments": "How many comments other players left on the song.",
    "Comment words": "Total words written in those voter comments.",
    "Crowd pleaser score": "A mix of strong points and lots of voters.",
    "Cult classic score": "Rewards strong votes from a smaller crowd.",
    "Vote disagreement": "How spread out the votes were. Lower means more agreement.",
    "Average vote": "Average points from people who voted on the song.",
    "Duration": "Spotify track length.",
}

def table(title, description, frame, columns, sort_column, ascending=False):
    st.subheader(title)
    st.caption(description)
    shown = frame.sort_values(sort_column, ascending=ascending).head(20)[columns].copy()
    config = {column: st.column_config.Column(column, help=COLUMN_HELP.get(column)) for column in columns}
    st.dataframe(shown, hide_index=True, use_container_width=True, column_config=config)

table("Biggest hits", "The songs with the most Music League points.", display, ["Track", "Artist", "Submitted by", "Round", "Points"], "Points")
table("Biggest flops", "The songs at the bottom of the points table.", display, ["Track", "Artist", "Submitted by", "Round", "Points", "Engagement rate"], "Points", True)
table("Most engaged", "Songs that got a vote from the biggest share of the room. Zeros and downvotes still count as voting.", display, ["Track", "Artist", "Submitted by", "Round", "Engagement rate", "People who voted", "People who could vote"], "Engagement rate")
table("Marmite", "Songs with the biggest gap between their highest and lowest votes. Downvotes count too.", display, ["Track", "Artist", "Submitted by", "Round", "Marmite spread", "Lowest vote", "Highest vote"], "Marmite spread")
table("Crowd pleasers", "Songs that did well and got most of the room involved.", display, ["Track", "Artist", "Submitted by", "Round", "Crowd pleaser score", "Points", "Engagement rate"], "Crowd pleaser score")
table("Cult classics", "Songs loved by a smaller group, even if the whole room did not vote for them.", display.dropna(subset=["Cult classic score"]), ["Track", "Artist", "Submitted by", "Round", "Cult classic score", "Average vote", "Engagement rate"], "Cult classic score")
table("Consensus picks", "Songs where the voters were most in agreement. Lower disagreement is better.", display.dropna(subset=["Vote disagreement"]), ["Track", "Artist", "Submitted by", "Round", "Vote disagreement", "Average vote", "People who voted"], "Vote disagreement", True)
table("Most discussed", "Songs that got people writing the most. The submitter's own note is not included.", display, ["Track", "Artist", "Submitted by", "Round", "Comment words", "Voter comments"], "Comment words")
if enrichment is not None and display.get("duration_ms", []).notna().any():
    table("Longest songs", "The tracks that kept going the longest.", display, ["Track", "Artist", "Submitted by", "Round", "Duration"], "duration_ms")
    table("Shortest songs", "The quickest tracks in the league.", display, ["Track", "Artist", "Submitted by", "Round", "Duration"], "duration_ms", True)
