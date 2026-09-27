import pandas as pd
from .config import PROCESSED_DIR

def load_data():
    names = ["players", "rounds", "submissions", "votes", "comments", "track_enrichment"]
    return {name: pd.read_parquet(PROCESSED_DIR / f"{name}.parquet") for name in names if (PROCESSED_DIR / f"{name}.parquet").exists()}
