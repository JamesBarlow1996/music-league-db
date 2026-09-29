import pandas as pd
from src.utils import parse_spotify_track_id, clean_text
from src.ingest import derive_round_ranks

def test_spotify_id_and_comments():
    assert parse_spotify_track_id("spotify:track:abc123") == "abc123"
    assert clean_text("  ") is None

def test_round_ranking_uses_voter_count_then_highest_vote():
    submissions = pd.DataFrame([
        {"submission_id": "a", "round_id": "r", "total_points": 4},
        {"submission_id": "b", "round_id": "r", "total_points": 4},
        {"submission_id": "c", "round_id": "r", "total_points": 4},
        {"submission_id": "d", "round_id": "r", "total_points": 4},
    ])
    votes = pd.DataFrame([
        {"submission_id": "a", "voter_player_id": "v1", "points": 3},
        {"submission_id": "a", "voter_player_id": "v2", "points": 1},
        {"submission_id": "b", "voter_player_id": "v1", "points": 2},
        {"submission_id": "b", "voter_player_id": "v2", "points": 2},
        {"submission_id": "c", "voter_player_id": "v1", "points": 4},
        {"submission_id": "d", "voter_player_id": "v1", "points": 3},
        {"submission_id": "d", "voter_player_id": "v2", "points": 1},
    ])
    ranked = derive_round_ranks(submissions, votes).set_index("submission_id")
    assert ranked.loc["a", "round_rank"] == 1
    assert ranked.loc["d", "round_rank"] == 1
    assert ranked.loc["b", "round_rank"] == 3
    assert ranked.loc["c", "round_rank"] == 4

def test_round_ranking_prefers_no_downvotes_before_highest_vote():
    submissions = pd.DataFrame([
        {"submission_id": "clean", "round_id": "r", "total_points": 3},
        {"submission_id": "downvoted", "round_id": "r", "total_points": 3},
    ])
    votes = pd.DataFrame([
        {"submission_id": "clean", "voter_player_id": "v1", "points": 2},
        {"submission_id": "clean", "voter_player_id": "v2", "points": 1},
        {"submission_id": "downvoted", "voter_player_id": "v1", "points": 3},
        {"submission_id": "downvoted", "voter_player_id": "v2", "points": 1},
        {"submission_id": "downvoted", "voter_player_id": "v3", "points": -1},
    ])
    ranked = derive_round_ranks(submissions, votes).set_index("submission_id")
    assert ranked.loc["clean", "round_rank"] == 1
    assert ranked.loc["downvoted", "round_rank"] == 2
