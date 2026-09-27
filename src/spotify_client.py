"""Small Spotify Web API client used only by the preprocessing step.

The export already contains Spotify track URIs, so direct ID lookup is the
primary path. Search is deliberately a fallback for malformed/missing URIs.
"""
import base64
import json
import time
from pathlib import Path
import requests
from .config import CACHE_DIR, setting

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_URL = "https://api.spotify.com/v1"

class SpotifyClient:
    def __init__(self, client_id=None, client_secret=None, cache_path=None, timeout=20):
        self.client_id = client_id or setting("SPOTIFY_CLIENT_ID")
        self.client_secret = client_secret or setting("SPOTIFY_CLIENT_SECRET")
        self.cache_path = Path(cache_path or CACHE_DIR / "spotify_cache.json")
        self.timeout = timeout
        self.enabled = bool(self.client_id and self.client_secret)
        self._token = None
        self._cache = self._read_cache()

    def _read_cache(self):
        if not self.cache_path.exists(): return {}
        try: return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, ValueError): return {}

    def _save_cache(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self._cache, indent=2), encoding="utf-8")

    def _access_token(self):
        if self._token: return self._token
        credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        response = requests.post(TOKEN_URL, headers={"Authorization": f"Basic {credentials}"}, data={"grant_type": "client_credentials"}, timeout=self.timeout)
        response.raise_for_status(); self._token = response.json()["access_token"]; return self._token

    def _get(self, path, params=None):
        response = requests.get(f"{API_URL}{path}", headers={"Authorization": f"Bearer {self._access_token()}"}, params=params, timeout=self.timeout)
        if response.status_code == 429:
            time.sleep(min(int(response.headers.get("Retry-After", "1")), 10)); response = requests.get(f"{API_URL}{path}", headers={"Authorization": f"Bearer {self._access_token()}"}, params=params, timeout=self.timeout)
        if response.status_code == 404: return None
        response.raise_for_status(); return response.json()

    def get_track(self, track_id):
        if not self.enabled or not track_id: return None
        key = f"track:{track_id}"
        if not self._cache.get(key):
            try:
                result = self._get(f"/tracks/{track_id}")
                if result: self._cache[key] = result; self._save_cache()
            except requests.RequestException: return None
        return self._cache.get(key)

    def search_track(self, track_name, artist_display):
        if not self.enabled or not track_name: return None
        key = f"search:{track_name.strip().lower()}|{(artist_display or '').strip().lower()}"
        if not self._cache.get(key):
            artist = artist_display or ""
            query = f'track:"{track_name}" artist:"{artist}"'
            try: result = self._get("/search", {"q": query, "type": "track", "limit": 1})
            except requests.RequestException: result = None
            match = (result or {}).get("tracks", {}).get("items", [None])[0]
            if match: self._cache[key] = match; self._save_cache()
        return self._cache.get(key)

    def get_artist(self, artist_id):
        if not self.enabled or not artist_id: return None
        key = f"artist:{artist_id}"
        if not self._cache.get(key):
            try:
                result = self._get(f"/artists/{artist_id}")
                if result: self._cache[key] = result; self._save_cache()
            except requests.RequestException: return None
        return self._cache.get(key)
