import hashlib
import re
import pandas as pd

def clean_text(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    return value or None

def parse_spotify_track_id(uri):
    if pd.isna(uri):
        return None
    match = re.match(r"^spotify:track:([A-Za-z0-9]+)$", str(uri).strip())
    return match.group(1) if match else None

def stable_id(*parts) -> str:
    return hashlib.sha256("|".join("" if p is None else str(p) for p in parts).encode()).hexdigest()[:16]

def utc_series(series):
    return pd.to_datetime(series, utc=True, errors="raise")
