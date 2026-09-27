"""Read and validate the four-file Music League export."""
from pathlib import Path
import json
import pandas as pd
from .config import RAW_DIR, PROCESSED_DIR
from .utils import clean_text, parse_spotify_track_id, stable_id, utc_series

FILES = {"competitors": "competitors.csv", "rounds": "rounds.csv", "submissions": "submissions.csv", "votes": "votes.csv"}

def _read(raw_dir=RAW_DIR):
    paths = {key: Path(raw_dir) / name for key, name in FILES.items()}
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing Music League export files: " + ", ".join(missing))
    return {key: pd.read_csv(path) for key, path in paths.items()}

def _require(df, columns, name):
    missing = set(columns) - set(df.columns)
    if missing:
        raise ValueError(f"{name} is missing columns: {sorted(missing)}")

def load_export(raw_dir=RAW_DIR):
    raw = _read(raw_dir)
    competitors, rounds = raw["competitors"].copy(), raw["rounds"].copy()
    submissions, votes = raw["submissions"].copy(), raw["votes"].copy()
    _require(competitors, ["ID", "Name"], "competitors.csv")
    _require(rounds, ["ID", "Created", "Name", "Description", "Playlist URL"], "rounds.csv")
    _require(submissions, ["Spotify URI", "Title", "Album", "Artist(s)", "Submitter ID", "Created", "Comment", "Round ID", "Visible To Voters"], "submissions.csv")
    _require(votes, ["Spotify URI", "Voter ID", "Created", "Points Assigned", "Comment", "Round ID"], "votes.csv")
    player_ids, round_ids = set(competitors["ID"]), set(rounds["ID"])
    if not set(submissions["Submitter ID"]).issubset(player_ids) or not set(votes["Voter ID"]).issubset(player_ids):
        raise ValueError("Found submission/vote player IDs absent from competitors.csv")
    if not set(submissions["Round ID"]).issubset(round_ids) or not set(votes["Round ID"]).issubset(round_ids):
        raise ValueError("Found submission/vote round IDs absent from rounds.csv")
    submissions["_key"] = list(zip(submissions["Round ID"], submissions["Spotify URI"]))
    votes["_key"] = list(zip(votes["Round ID"], votes["Spotify URI"], votes["Voter ID"]))
    if submissions["_key"].duplicated().any(): raise ValueError("Duplicate round_id + spotify_uri in submissions")
    if votes["_key"].duplicated().any(): raise ValueError("Duplicate round_id + spotify_uri + voter_id in votes")
    submitter_by_key = submissions.set_index(["Round ID", "Spotify URI"])["Submitter ID"]
    self_votes = votes.apply(lambda r: submitter_by_key.get((r["Round ID"], r["Spotify URI"])) == r["Voter ID"], axis=1)
    if self_votes.any(): raise ValueError("Explicit self-vote rows are not supported")
    rounds_n = pd.DataFrame({"round_id": rounds["ID"], "round_name": rounds["Name"], "round_description": rounds["Description"], "round_created_at": utc_series(rounds["Created"]), "playlist_url": rounds["Playlist URL"]})
    rounds_n = rounds_n.sort_values("round_created_at").reset_index(drop=True); rounds_n["round_number"] = rounds_n.index + 1
    players = pd.DataFrame({"player_id": competitors["ID"], "player_name": competitors["Name"]})
    active = set(submissions["Submitter ID"]) | set(votes["Voter ID"]); players["active_flag"] = players.player_id.isin(active)
    sub = pd.DataFrame({"round_id": submissions["Round ID"], "player_id": submissions["Submitter ID"], "spotify_uri": submissions["Spotify URI"], "spotify_track_id": submissions["Spotify URI"].map(parse_spotify_track_id), "track_name": submissions["Title"], "artist_display": submissions["Artist(s)"], "album_name": submissions["Album"], "submitted_at": utc_series(submissions["Created"]), "submission_comment": submissions["Comment"].map(clean_text), "visible_to_voters": submissions["Visible To Voters"].astype(str).str.strip().str.lower().isin(["yes", "true", "1"])})
    sub["submission_id"] = [stable_id(r, u) for r, u in zip(sub.round_id, sub.spotify_uri)]
    sub = sub[["submission_id", "round_id", "player_id", "spotify_uri", "spotify_track_id", "track_name", "artist_display", "album_name", "submitted_at", "submission_comment", "visible_to_voters"]]
    vote = pd.DataFrame({"round_id": votes["Round ID"], "spotify_uri": votes["Spotify URI"], "voter_player_id": votes["Voter ID"], "voted_at": utc_series(votes["Created"]), "points": pd.to_numeric(votes["Points Assigned"], errors="raise").astype(int), "vote_comment": votes["Comment"].map(clean_text)})
    vote["submission_id"] = [stable_id(r, u) for r, u in zip(vote.round_id, vote.spotify_uri)]
    vote["submitted_by_player_id"] = vote.apply(lambda x: submitter_by_key[(x.round_id, x.spotify_uri)], axis=1)
    vote = vote[["round_id", "submission_id", "voter_player_id", "submitted_by_player_id", "voted_at", "points", "vote_comment"]]
    sub["total_points"] = sub.submission_id.map(vote.groupby("submission_id").points.sum()).fillna(0).astype(int)
    sub["round_rank"] = sub.groupby("round_id").total_points.rank(method="min", ascending=False).astype(int)
    comments = []
    for row in sub.itertuples():
        if row.submission_comment: comments.append({"comment_id": stable_id(row.submission_id, row.player_id, "submission"), "round_id": row.round_id, "submission_id": row.submission_id, "commenter_player_id": row.player_id, "comment_type": "submission_note", "comment_text": row.submission_comment, "created_at": row.submitted_at})
    for row in vote.dropna(subset=["vote_comment"]).itertuples():
        comments.append({"comment_id": stable_id(row.submission_id, row.voter_player_id, row.voted_at), "round_id": row.round_id, "submission_id": row.submission_id, "commenter_player_id": row.voter_player_id, "comment_type": "vote_comment", "comment_text": row.vote_comment, "created_at": row.voted_at})
    comments = pd.DataFrame(comments, columns=["comment_id", "round_id", "submission_id", "commenter_player_id", "comment_type", "comment_text", "created_at"])
    if not comments.empty:
        comments["comment_word_count"] = comments.comment_text.str.split().str.len(); comments["comment_char_count"] = comments.comment_text.str.len()
    else: comments = pd.DataFrame(columns=["comment_id", "round_id", "submission_id", "commenter_player_id", "comment_type", "comment_text", "created_at", "comment_word_count", "comment_char_count"])
    report = {"player_count": len(players), "round_count": len(rounds_n), "submission_count": len(sub), "vote_count": len(vote), "submissions_per_round": sub.groupby("round_id").size().to_dict(), "voters_per_round": vote.groupby("round_id").voter_player_id.nunique().to_dict(), "point_distribution": vote.points.value_counts().sort_index().to_dict(), "self_vote_count": 0}
    return {"players": players, "rounds": rounds_n, "submissions": sub, "votes": vote, "comments": comments, "validation_report": report}

def write_tables(tables, output_dir=PROCESSED_DIR):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    report = tables.pop("validation_report", {})
    for name, frame in tables.items(): frame.to_parquet(Path(output_dir) / f"{name}.parquet", index=False)
    (Path(output_dir) / "validation_report.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

if __name__ == "__main__": write_tables(load_export())
