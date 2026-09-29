# Music League Dashboard

Mobile-friendly Streamlit analytics for Music League exports.

## Quick start

1. Copy `competitors.csv`, `rounds.csv`, `submissions.csv`, and `votes.csv` into `data/raw/`.
2. Install dependencies: `pip install -r requirements.txt`.
3. Build processed data: `python refresh_data.py`.
4. Run: `streamlit run app.py`.

Spotify is the first enrichment source. The refresh uses the exact `spotify:track:<id>` from each submission with the Spotify Web API track endpoint, then falls back to Spotify search only when the ID is missing or unavailable. It caches responses in `data/cache/spotify_cache.json` and writes `data/processed/track_enrichment.parquet`. Set `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in `.env` before refreshing. Native metrics work without API keys. Round positions are ordered by total points, distinct positive voters, fewest downvoters, then highest single positive vote; exact matches use competition ranking (`1, 1, 3`). Explicit zero-point votes count as engagement while missing rows do not.

## Deploy to Streamlit Community Cloud

1. Commit the project to GitHub. The processed Parquet files are included; raw CSV files, API credentials, and API caches are ignored.
2. Open https://share.streamlit.io and connect the GitHub account that owns the repository.
3. Choose **Create app**, select the repository and branch, and use `app.py` as the entrypoint.
4. Choose Python 3.12 in Advanced settings. Spotify secrets are not needed at runtime because enrichment happens locally before deployment.
5. Deploy, make the app public in its Sharing settings, and send the resulting `streamlit.app` URL to friends.

When league data changes, replace the local raw CSV files, run `python refresh_data.py`, then commit and push the updated files in `data/processed/`.
