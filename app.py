import streamlit as st
import streamlit.components.v1 as components
from html import escape
from src.dashboard import load_data
from src.metrics import player_summary, song_metrics
from src.player_cards import build_player_cards
from src.theme import apply_retro_theme

st.set_page_config(page_title="Paddys leaving clinks music league", page_icon="🎵", layout="wide")
apply_retro_theme()

data = load_data()
if not data or "submissions" not in data:
    st.markdown('<div class="wordart-title">Paddys leaving clinks music league</div>', unsafe_allow_html=True)
    st.info("Drop the four CSV exports into data/raw, then run python refresh_data.py."); st.stop()
players, submissions, votes = data["players"], data["submissions"], data["votes"]
summary = player_summary(submissions, players); songs = song_metrics(submissions, votes, players)
st.markdown('<div class="wordart-title">Paddys leaving clinks music league</div>', unsafe_allow_html=True)
st.markdown('<div class="marquee-box"><span class="marquee-text">★ WELCOME TO THE MUSIC ZONE ★ BEST VIEWED WITH HEADPHONES ★ NOW WITH 100% MORE SPREADSHEETS ★</span></div>', unsafe_allow_html=True)
intro, dog = st.columns([1, 1.15])
with intro:
    st.markdown('<div class="retro-slogan">100% pretty neat</div><div class="retro-orange">FREE!</div><br><br><div class="retro-purple">phat stats</div><br><br><div class="retro-outline">Remember good music?</div><br><br><span class="visitor">YOU ARE VISITOR #000027</span><p class="blink">● SITE UNDER CONSTRUCTION ●</p>', unsafe_allow_html=True)
with dog:
    st.image("assets/logos/headphone-dog.png", caption="Official league listening expert", width="stretch")
rounds = data.get("rounds")
if rounds is not None and "playlist_url" in rounds.columns and rounds["playlist_url"].notna().any():
    st.markdown('<div class="retro-purple">JUKEBOX 95</div>', unsafe_allow_html=True)
    st.caption("Pick a round, press play, and enjoy the highly professional soundtrack.")
    playable = rounds.dropna(subset=["playlist_url"])
    chosen_round = st.selectbox("Choose a playlist", playable["round_name"].tolist())
    playlist_url = playable.loc[playable["round_name"] == chosen_round, "playlist_url"].iloc[0]
    embed_url = playlist_url.replace("open.spotify.com/", "open.spotify.com/embed/")
    components.html(f'''<div style="border:7px ridge #d8d8d8;background:#c0c0c0;padding:6px;box-shadow:6px 6px 0 #5454a8;"><iframe title="Spotify playlist for {escape(chosen_round)}" src="{escape(embed_url)}" width="100%" height="352" frameborder="0" allowfullscreen allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe></div>''', height=380)
c1,c2,c3,c4 = st.columns(4); c1.metric("Players", len(players)); c2.metric("Rounds", submissions.round_id.nunique()); c3.metric("Songs", len(submissions)); c4.metric("Explicit votes", len(votes))
st.subheader("Overall standings")
st.dataframe(summary[["rank","player_name","total_points","average_points","wins","podiums"]].rename(columns={"rank":"Rank","player_name":"Player","total_points":"Points","average_points":"Avg / song","wins":"Wins","podiums":"Podiums"}), hide_index=True, use_container_width=True)
st.subheader("Featured awards")
award_cols = st.columns(3)
for col, (label, row) in zip(award_cols, [("Biggest Hit", songs.loc[songs.total_points.idxmax()]), ("Biggest Flop", songs.loc[songs.total_points.idxmin()]), ("Most Engaged", songs.loc[songs.engagement_rate.idxmax()])]):
    col.markdown(f'<div class="retro-card"><b>{label}</b><br>{row.track_name}<br><small>{row.artist_display} · {int(row.total_points)} points</small></div>', unsafe_allow_html=True)
