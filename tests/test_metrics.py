import pandas as pd
from src.metrics import song_metrics
def test_engagement_counts_explicit_zero():
    subs=pd.DataFrame([{"submission_id":"s","round_id":"r","player_id":"a","total_points":0,"track_name":"x","artist_display":"y"}])
    votes=pd.DataFrame([{"submission_id":"s","round_id":"r","voter_player_id":"b","points":0,"vote_comment":None}])
    players=pd.DataFrame([{"player_id":"a"},{"player_id":"b"}])
    assert song_metrics(subs,votes,players).iloc[0].engagement_rate == 1

def test_marmite_uses_full_vote_spread():
    subs=pd.DataFrame([{"submission_id":"s","round_id":"r","player_id":"a","total_points":2,"track_name":"x","artist_display":"y"},{"submission_id":"other","round_id":"r","player_id":"b","total_points":0,"track_name":"z","artist_display":"q"}])
    votes=pd.DataFrame([{"submission_id":"s","round_id":"r","voter_player_id":"b","points":3,"vote_comment":None},{"submission_id":"s","round_id":"r","voter_player_id":"c","points":-2,"vote_comment":None}])
    players=pd.DataFrame([{"player_id":"a"},{"player_id":"b"},{"player_id":"c"}])
    result= song_metrics(subs,votes,players).set_index("submission_id")
    assert result.loc["s", "marmite_spread"] == 5
