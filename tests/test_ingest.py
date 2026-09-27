from src.utils import parse_spotify_track_id, clean_text
def test_spotify_id_and_comments():
    assert parse_spotify_track_id("spotify:track:abc123") == "abc123"
    assert clean_text("  ") is None
