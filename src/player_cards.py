import pandas as pd
from .metrics import percentile

def build_player_cards(summary, submissions, comments=None):
    cards = summary.copy()
    cards["PFM"] = (0.40 * percentile(cards["average_points"]) + 0.25 * percentile(cards["wins"]) + 0.20 * percentile(cards["podiums"]) + 0.15 * (1 - percentile(cards["rank"]))).fillna(0)
    artist_counts = submissions.groupby("player_id").agg(unique_artists=("artist_display", "nunique"), total=("submission_id", "count"))
    cards = cards.merge(artist_counts, how="left", left_on="player_id", right_index=True); cards["TST"] = (cards["unique_artists"] / cards["total"].replace(0, 1)).fillna(0)
    if comments is None: cards["VOC"] = 0
    else:
        words = comments.groupby("commenter_player_id").comment_word_count.sum(); cards["VOC"] = cards["player_id"].map(words).fillna(0); cards["VOC"] = percentile(cards["VOC"])
    cards["VOT"] = percentile(cards["submissions"]); cards["DVG"] = 0.5; cards["RNG"] = cards["TST"]
    for col in ["PFM", "TST", "VOC", "VOT", "DVG", "RNG"]: cards[col] = (40 + 59 * cards[col].clip(0, 1)).round().astype(int)
    cards["OVR"] = (0.35*cards["PFM"] + 0.20*cards["TST"] + 0.15*cards["VOC"] + 0.10*cards["VOT"] + 0.10*cards["DVG"] + 0.10*cards["RNG"]).round().astype(int)
    cards["archetype"] = cards.apply(lambda r: "Most Vocal" if r["VOC"] == cards["VOC"].max() else ("Explorer" if r["TST"] == cards["TST"].max() else "League Regular"), axis=1); return cards
