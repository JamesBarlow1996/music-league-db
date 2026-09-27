import streamlit as st
from src.dashboard import load_data
from src.metrics import player_summary
from src.player_cards import build_player_cards
from src.theme import apply_retro_theme

data = load_data()
apply_retro_theme()
st.title("Players")
if "submissions" not in data or "players" not in data:
    st.info("Run refresh_data.py first to create the processed tables.")
    st.stop()

summary = player_summary(data["submissions"], data["players"])
cards = build_player_cards(summary, data["submissions"], data.get("comments"))
st.subheader("Player card stats")
st.caption("These are playful scores out of 99, based on what each person submitted, voted for, and commented on.")
st.table([
    {"Card label": "OVR", "In plain English": "Overall score combining the other ratings."},
    {"Card label": "PFM", "In plain English": "How well this person’s songs have performed."},
    {"Card label": "TST", "In plain English": "How varied their choice of artists is."},
    {"Card label": "VOC", "In plain English": "How much they talk and comment."},
    {"Card label": "VOT", "In plain English": "How actively they vote on other people’s songs."},
    {"Card label": "DVG", "In plain English": "How much their songs divide opinion."},
    {"Card label": "RNG", "In plain English": "How wide a mix of artists and musical eras they choose."},
])
for start in range(0,len(cards),3):
    cols=st.columns(3)
    for col,(_, row) in zip(cols,cards.iloc[start:start+3].iterrows()):
        col.markdown(f"""
        <div style="border:6px ridge #d8d8d8;padding:18px;margin:6px 0 18px;background:linear-gradient(145deg,#ffffff,#dcecff);box-shadow:6px 6px 0 #5454a8;color:#111;">
        <h3 style="margin:0 0 6px 0;">{row.player_name}</h3>
        <div style="font-size:1.05rem;"><b>OVR {row.OVR}</b></div>
        <hr style="border-color:#555b86;">
        <div><b>PFM</b> {row.PFM} &nbsp; <b>TST</b> {row.TST} &nbsp; <b>VOC</b> {row.VOC}</div>
        <div><b>VOT</b> {row.VOT} &nbsp; <b>DVG</b> {row.DVG} &nbsp; <b>RNG</b> {row.RNG}</div>
        <p style="margin:12px 0 0 0;">{int(row.total_points)} points · {int(row.wins)} wins · {int(row.podiums)} podiums</p>
        </div>
        """, unsafe_allow_html=True)
st.divider()
name = st.selectbox("Player profile", cards.player_name.tolist())
p = cards.loc[cards.player_name == name].iloc[0]
st.subheader(p.player_name)
st.write(f"Rank {int(p['rank'])} · {int(p.total_points)} points · {float(p.average_points):.1f} average · {int(p.podiums)} podiums")
profile = data["submissions"].loc[data["submissions"]["player_id"] == p["player_id"], ["round_id","track_name","artist_display","total_points","round_rank"]].copy()
st.dataframe(profile, hide_index=True, use_container_width=True)
