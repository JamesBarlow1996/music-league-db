import streamlit as st
from src.dashboard import load_data
from src.metrics import player_summary, song_metrics, participating_players
from src.player_cards import build_player_cards
from src.theme import apply_retro_theme

st.set_page_config(page_title="Paddys leaving clinks music league", page_icon="🎵", layout="wide")
apply_retro_theme()

data = load_data()
if not data or "submissions" not in data:
    st.markdown('<div class="wordart-title">Paddys leaving clinks music league</div>', unsafe_allow_html=True)
    st.info("Drop the four CSV exports into data/raw, then run python refresh_data.py."); st.stop()
players, submissions, votes = data["players"], data["submissions"], data["votes"]
award_players = participating_players(players, submissions)
summary = player_summary(submissions, award_players); songs = song_metrics(submissions, votes, award_players)
st.markdown('<div class="wordart-title">Paddys leaving clinks music league</div>', unsafe_allow_html=True)
st.markdown('<div class="marquee-box"><span class="marquee-text">★ WELCOME TO THE MUSIC LEAGUE ★ DIG INTO SOME MUSIC LEAGUE METRICS ★ MUSIC IS THE WINNER ★</span></div>', unsafe_allow_html=True)
intro, dog = st.columns([1, 1.15])
with intro:
    st.markdown('<div class="retro-slogan">100% pretty neat</div><div class="retro-orange">FREE!</div><br><br><div class="retro-purple">phat stats</div><br><br><div class="retro-outline">Remember good music?</div><br><br><span class="visitor">YOU ARE VISITOR #000027</span><p class="blink">● EAGER MEAGER ●</p>', unsafe_allow_html=True)
with dog:
    st.image("assets/logos/headphone-dog.png", caption="Wowe this song is shite", width="stretch")
c1,c2,c3,c4 = st.columns(4); c1.metric("Players", len(players)); c2.metric("Rounds", submissions.round_id.nunique()); c3.metric("Songs", len(submissions)); c4.metric("Explicit votes", len(votes))
st.subheader("Overall standings")
st.dataframe(summary[["rank","player_name","total_points","average_points","wins","podiums"]].rename(columns={"rank":"Rank","player_name":"Player","total_points":"Points","average_points":"Avg / song","wins":"Wins","podiums":"Podiums"}), hide_index=True, use_container_width=True)
st.subheader("Featured awards")
award_cols = st.columns(3)
for col, (label, row) in zip(award_cols, [("Biggest Hit", songs.loc[songs.total_points.idxmax()]), ("Biggest Flop", songs.loc[songs.total_points.idxmin()]), ("Most Engaged", songs.loc[songs.engagement_rate.idxmax()])]):
    col.markdown(f'<div class="retro-card"><b>{label}</b><br>{row.track_name}<br><small>{row.artist_display} · {int(row.total_points)} points</small></div>', unsafe_allow_html=True)

rounds = data.get("rounds")
if rounds is not None and not rounds.empty:
    latest_round = rounds.sort_values("round_number").iloc[-1]
    latest_songs = submissions.loc[submissions["round_id"] == latest_round["round_id"]].sort_values(["total_points", "track_name"], ascending=[False, True])
    if not latest_songs.empty and latest_songs.iloc[0]["spotify_track_id"]:
        winner = latest_songs.iloc[0]
        st.markdown('<div class="retro-purple">JUKEBOX 95</div>', unsafe_allow_html=True)
        st.markdown(f'**Latest round winner:** {winner["track_name"]} — {winner["artist_display"]}')
        st.caption(f'{latest_round["round_name"]} · {int(winner["total_points"])} points · press play below')
        st.iframe(f'https://open.spotify.com/embed/track/{winner["spotify_track_id"]}', width="stretch", height=152)
