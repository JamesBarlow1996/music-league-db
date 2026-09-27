"""Spotify-first enrichment refresh. Core dashboard remains functional without keys."""
from datetime import datetime, timezone
import pandas as pd
from .config import PROCESSED_DIR
from .spotify_client import SpotifyClient

ENRICHMENT_COLUMNS = ["spotify_track_id", "spotify_uri", "spotify_artist_id", "popularity_score", "popularity_source", "popularity_retrieved_at", "duration_ms", "release_date", "release_year", "decade", "explicit", "genres", "lastfm_tags", "musicbrainz_recording_id", "match_source", "match_confidence"]

def _year(value):
    try: return int(str(value)[:4])
    except (TypeError, ValueError): return None

def _row(track, submission, source, confidence, genres=None):
    if not track: return {"spotify_track_id": submission.spotify_track_id, "spotify_uri": submission.spotify_uri, "match_source": source, "match_confidence": confidence}
    album = track.get("album") or {}; artists = track.get("artists") or []; artist = artists[0] if artists else {}
    release_date = album.get("release_date"); year = _year(release_date)
    return {"spotify_track_id": submission.spotify_track_id or track.get("id"), "spotify_uri": submission.spotify_uri, "spotify_artist_id": artist.get("id"), "popularity_score": track.get("popularity"), "popularity_source": "spotify", "popularity_retrieved_at": datetime.now(timezone.utc).isoformat(), "duration_ms": track.get("duration_ms"), "release_date": release_date, "release_year": year, "decade": (year // 10) * 10 if year else None, "explicit": track.get("explicit"), "genres": "|".join(genres or []) or None, "lastfm_tags": None, "musicbrainz_recording_id": None, "match_source": source, "match_confidence": confidence}

def enrich_tracks(submissions, client=None, manual_overrides=None):
    client = client or SpotifyClient(); overrides = manual_overrides or {}
    rows = []
    for submission in submissions.drop_duplicates("spotify_uri").itertuples():
        track = None; source = "unmatched"; confidence = 0.0
        override = overrides.get(submission.submission_id)
        if override and override.get("source") == "spotify": track = client.get_track(override.get("external_track_id")); source, confidence = "manual_override", 1.0
        if track is None and submission.spotify_track_id: track = client.get_track(submission.spotify_track_id); source, confidence = "spotify_uri", 1.0
        if track is None: track = client.search_track(submission.track_name, submission.artist_display); source, confidence = ("spotify_search", 0.85) if track else ("unmatched", 0.0)
        genres = []
        if track and track.get("artists"):
            artist = client.get_artist(track["artists"][0].get("id"))
            genres = (artist or {}).get("genres", [])
        rows.append(_row(track, submission, source, confidence, genres))
    return pd.DataFrame(rows).reindex(columns=ENRICHMENT_COLUMNS)

def write_enrichment(enrichment, output_dir=PROCESSED_DIR): enrichment.to_parquet(output_dir / "track_enrichment.parquet", index=False)

if __name__ == "__main__":
    from .ingest import load_export
    write_enrichment(enrich_tracks(load_export()["submissions"]))
