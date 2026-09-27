from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
CACHE_DIR = ROOT / "data" / "cache"
for _directory in (RAW_DIR, PROCESSED_DIR, CACHE_DIR):
    _directory.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT / ".env")

def setting(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)
