"""Explainable Music League metrics. Functions accept normalized DataFrames."""
import numpy as np
import pandas as pd

def vote_opportunities(submissions, votes, players):
    rows = []
    for round_id, group in submissions.groupby("round_id"):
        # Include submitters plus anyone who explicitly voted in the round.
        submitters = set(group["player_id"].dropna())
        voters = set(votes.loc[votes["round_id"] == round_id, "voter_player_id"].dropna())
        eligible = list(submitters | voters)
        for sub in group.itertuples():
            for voter in eligible:
                if voter != sub.player_id:
                    rows.append({"round_id": round_id, "submission_id": sub.submission_id, "voter_player_id": voter})
    dense = pd.DataFrame(rows, columns=["round_id", "submission_id", "voter_player_id"])
    if dense.empty: return dense.assign(points_effective=pd.Series(dtype=float), explicit_vote_flag=pd.Series(dtype=bool))
    explicit = votes[["round_id", "submission_id", "voter_player_id", "points"]].copy(); explicit["explicit_vote_flag"] = True
    dense = dense.merge(explicit, how="left", on=["round_id", "submission_id", "voter_player_id"])
    dense["explicit_vote_flag"] = dense.explicit_vote_flag.fillna(False).astype(bool); dense["points_effective"] = dense.points.fillna(0); return dense

def player_summary(submissions, players):
    s = submissions.groupby("player_id").agg(total_points=("total_points", "sum"), submissions=("submission_id", "count"), average_points=("total_points", "mean"), wins=("round_rank", lambda x: (x == 1).sum()), podiums=("round_rank", lambda x: (x <= 3).sum())).reset_index()
    out = players[["player_id", "player_name"]].merge(s, how="left").fillna({"total_points": 0, "submissions": 0, "average_points": 0, "wins": 0, "podiums": 0})
    out["rank"] = out.total_points.rank(method="min", ascending=False).astype(int); return out.sort_values(["rank", "player_name"])

def song_metrics(submissions, votes, players):
    dense = vote_opportunities(submissions, votes, players)
    prepared = votes.copy()
    prepared["comment_words"] = prepared["vote_comment"].fillna("").astype(str).str.split().str.len()
    v = prepared.groupby("submission_id").agg(explicit_voters=("voter_player_id", "nunique"), vote_count=("points", "size"), vote_std=("points", "std"), vote_min=("points", "min"), vote_max=("points", "max"), avg_explicit_vote=("points", "mean"), voter_comment_count=("vote_comment", lambda x: x.notna().sum()), voter_comment_words=("comment_words", "sum"), voter_commenters=("voter_player_id", lambda x: x[prepared.loc[x.index, "vote_comment"].notna()].nunique())).reset_index()
    eligible = dense.groupby("submission_id").size().rename("eligible_voters"); result = submissions.merge(v, how="left").merge(eligible, how="left", left_on="submission_id", right_index=True)
    for col in ["explicit_voters", "vote_count", "voter_comment_count", "voter_comment_words", "voter_commenters"]: result[col] = result[col].fillna(0).astype(int)
    result["eligible_voters"] = result["eligible_voters"].fillna(0).astype(int)
    result["engagement_rate"] = result["explicit_voters"].div(result["eligible_voters"].replace(0, np.nan)).fillna(0)
    result["marmite_spread"] = (result["vote_max"] - result["vote_min"]).fillna(0)
    result["vote_std"] = result["vote_std"].fillna(0)
    result["points_percentile"] = percentile(result["total_points"])
    result["engagement_percentile"] = percentile(result["engagement_rate"])
    result["avg_vote_percentile"] = percentile(result["avg_explicit_vote"])
    result["crowd_pleaser_score"] = 0.5 * result["points_percentile"] + 0.5 * result["engagement_percentile"]
    result["cult_classic_score"] = result["avg_vote_percentile"] * (1 - result["engagement_rate"])
    result.loc[(result["avg_explicit_vote"] <= 0) | (result["explicit_voters"] < 2), "cult_classic_score"] = np.nan
    result["consensus_score"] = result["vote_std"]
    result.loc[(result["explicit_voters"] < 2) | (result["engagement_rate"] < 0.25), "consensus_score"] = np.nan
    return result

def relationships(submissions, votes, players):
    dense = vote_opportunities(submissions, votes, players).merge(submissions[["submission_id", "player_id"]], on="submission_id")
    records = []
    for recipient, group in dense.groupby("player_id"):
        for voter, pair in group.groupby("voter_player_id"):
            if voter != recipient: records.append({"recipient_player_id": recipient, "voter_player_id": voter, "normalized_support": pair.points_effective.sum() / len(pair), "raw_points": pair.points_effective.sum(), "opportunities": len(pair)})
    return pd.DataFrame(records)

def voting_summary(votes, players):
    grouped = votes.groupby("voter_player_id").agg(votes_cast=("points", "size"), average_points_given=("points", "mean"), total_points_given=("points", "sum"), positive_vote_rate=("points", lambda x: (x > 0).mean()), negative_vote_rate=("points", lambda x: (x < 0).mean())).reset_index()
    return players[["player_id", "player_name"]].merge(grouped, left_on="player_id", right_on="voter_player_id", how="left").drop(columns="voter_player_id").fillna(0)

def kingmaker_summary(submissions, votes, players):
    winners = submissions.loc[submissions["round_rank"] == 1, ["round_id", "submission_id", "player_id"]].rename(columns={"player_id": "winner_player_id"})
    rows = []
    for player in players.itertuples():
        eligible = winners.loc[winners["winner_player_id"] != player.player_id]
        backed = votes.merge(eligible[["round_id", "submission_id"]], on=["round_id", "submission_id"], how="inner")
        count = backed.loc[(backed["voter_player_id"] == player.player_id) & (backed["points"] > 0), "round_id"].nunique()
        rows.append({"player_id": player.player_id, "player_name": player.player_name, "winners_backed": count, "eligible_rounds": eligible["round_id"].nunique()})
    result = pd.DataFrame(rows)
    result["kingmaker_rate"] = result["winners_backed"].div(result["eligible_rounds"].replace(0, np.nan)).fillna(0)
    return result

def comment_summary(comments, players):
    if comments is None or comments.empty:
        result = players[["player_id", "player_name"]].copy()
        for col in ["comment_count", "total_words", "average_words", "submissions_commented_on"]: result[col] = 0
        return result
    all_comments = comments.groupby("commenter_player_id").agg(comment_count=("comment_id", "count"), total_words=("comment_word_count", "sum"), average_words=("comment_word_count", "mean")).reset_index()
    vote_comments = comments.loc[comments["comment_type"] == "vote_comment"].groupby("commenter_player_id")["submission_id"].nunique().rename("submissions_commented_on").reset_index()
    result = players[["player_id", "player_name"]].merge(all_comments, left_on="player_id", right_on="commenter_player_id", how="left").drop(columns="commenter_player_id").merge(vote_comments, left_on="player_id", right_on="commenter_player_id", how="left").drop(columns="commenter_player_id")
    return result.fillna({"comment_count": 0, "total_words": 0, "average_words": 0, "submissions_commented_on": 0})

def player_song_summary(submissions, votes, players):
    songs = song_metrics(submissions, votes, players)
    records = songs.groupby("player_id").agg(average_engagement=("engagement_rate", "mean"), average_marmite=("marmite_spread", "mean"), most_marmite_song=("marmite_spread", "max")).reset_index()
    return player_summary(submissions, players).merge(records, on="player_id", how="left")

def taste_summary(submissions, enrichment, players):
    data = submissions.merge(enrichment, on=["spotify_track_id", "spotify_uri"], how="left")
    data["submission_year"] = pd.to_datetime(data["submitted_at"], utc=True, errors="coerce").dt.year
    data["track_age_at_submission"] = data["submission_year"] - data["release_year"]
    grouped = data.groupby("player_id").agg(average_popularity=("popularity_score", "mean"), average_release_year=("release_year", "mean"), oldest_release=("release_year", "min"), newest_release=("release_year", "max"), average_track_age=("track_age_at_submission", "mean"), total_submissions=("submission_id", "count"), unique_artists=("artist_display", "nunique")).reset_index()
    grouped["release_year_range"] = grouped["newest_release"] - grouped["oldest_release"]
    grouped["artist_diversity"] = grouped["unique_artists"].div(grouped["total_submissions"].replace(0, np.nan))
    grouped["repeat_rate"] = 1 - grouped["artist_diversity"]
    decade_counts = data.dropna(subset=["decade"]).groupby(["player_id", "decade"]).size().rename("count").reset_index()
    if decade_counts.empty:
        grouped["top_decade"] = np.nan; grouped["decade_share"] = np.nan
    else:
        idx = decade_counts.groupby("player_id")["count"].idxmax()
        top = decade_counts.loc[idx].rename(columns={"decade": "top_decade", "count": "top_decade_count"})
        grouped = grouped.merge(top[["player_id", "top_decade", "top_decade_count"]], on="player_id", how="left")
        grouped["decade_share"] = grouped["top_decade_count"].div(grouped["total_submissions"])
    genre_rows = []
    if "genres" in data.columns:
        for row in data[["player_id", "genres"]].dropna(subset=["genres"]).itertuples(index=False):
            values = row.genres if isinstance(row.genres, (list, tuple, np.ndarray)) else str(row.genres).split("|")
            for genre in values:
                genre = str(genre).strip().lower()
                if genre: genre_rows.append({"player_id": row.player_id, "genre": genre})
    if genre_rows:
        genre_counts = pd.DataFrame(genre_rows).groupby(["player_id", "genre"]).size().rename("count").reset_index()
        totals = genre_counts.groupby("player_id")["count"].sum().rename("genre_total")
        top = genre_counts.loc[genre_counts.groupby("player_id")["count"].idxmax()].rename(columns={"genre": "top_genre", "count": "top_genre_count"})
        grouped = grouped.merge(top[["player_id", "top_genre", "top_genre_count"]], on="player_id", how="left").merge(totals, on="player_id", how="left")
        grouped["genre_share"] = grouped["top_genre_count"].div(grouped["genre_total"])
    else:
        grouped["top_genre"] = np.nan; grouped["genre_share"] = np.nan
    return players[["player_id", "player_name"]].merge(grouped, on="player_id", how="left"), data

def percentile(series):
    return series.rank(pct=True, method="average").fillna(0)

def popularity_awards(submissions, enrichment):
    data = submissions.merge(enrichment, on=["spotify_track_id", "spotify_uri"], how="left")
    if "popularity_score" not in data: return data
    data["popularity_percentile"] = percentile(data.popularity_score); data["points_percentile"] = percentile(data.total_points); data["hidden_gem_score"] = data.points_percentile - data.popularity_percentile; data["mainstream_flop_score"] = data.popularity_percentile - data.points_percentile; return data

if __name__ == "__main__":
    from .config import PROCESSED_DIR
    tables = {name: pd.read_parquet(PROCESSED_DIR / f"{name}.parquet") for name in ["players", "submissions", "votes"]}
    player_summary(tables["submissions"], tables["players"]).to_parquet(PROCESSED_DIR / "player_summary.parquet", index=False)
    song_metrics(tables["submissions"], tables["votes"], tables["players"]).to_parquet(PROCESSED_DIR / "song_metrics.parquet", index=False)
