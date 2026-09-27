from src.ingest import load_export, write_tables
from src.enrich import enrich_tracks, write_enrichment
from src.config import ROOT
import pandas as pd

def load_manual_overrides():
    path = ROOT / "data" / "manual_track_matches.csv"
    if not path.exists(): return {}
    frame = pd.read_csv(path).fillna("")
    return {row.submission_id: row._asdict() for row in frame.itertuples(index=False)}

if __name__ == "__main__":
    tables = load_export(); enrichment = enrich_tracks(tables["submissions"], manual_overrides=load_manual_overrides()); write_tables(tables); write_enrichment(enrichment)
    print("Processed Music League data written to data/processed")
