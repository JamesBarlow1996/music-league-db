"""Compatibility entry point for normalization; ingestion performs cleaning."""
from .ingest import load_export, write_tables

def normalize(raw_dir=None, output_dir=None):
    return write_tables(load_export(raw_dir) if raw_dir else load_export(), output_dir) if output_dir else load_export(raw_dir) if raw_dir else load_export()
