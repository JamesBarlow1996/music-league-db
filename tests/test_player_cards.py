import pandas as pd
from src.player_cards import build_player_cards
def test_cards_have_stats():
    summary=pd.DataFrame([{"player_id":"a","player_name":"A","total_points":4,"submissions":1,"average_points":4,"wins":1,"podiums":1,"rank":1}])
    subs=pd.DataFrame([{"player_id":"a","submission_id":"s","artist_display":"X"}])
    card=build_player_cards(summary,subs)
    assert card.iloc[0].OVR >= 40
