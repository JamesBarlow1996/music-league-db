import streamlit as st

def apply_retro_theme():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #fffdf0;
            background-image: radial-gradient(#b7e4ff 1px, transparent 1px), radial-gradient(#ffd1e6 1px, transparent 1px);
            background-position: 0 0, 12px 12px;
            background-size: 24px 24px;
            color: #111;
        }
        .block-container { max-width: 1180px; padding-top: 1.4rem; }
        [data-testid="stSidebar"] { background: #c0c0c0; border-right: 5px ridge #fff; }
        [data-testid="stSidebar"] * { color: #111 !important; font-family: "Comic Sans MS", Arial, sans-serif; }
        h1, h2, h3 { font-family: "Trebuchet MS", Arial, sans-serif !important; color: #121269 !important; text-shadow: 2px 2px #8fe8ff; }
        p, label, [data-testid="stCaptionContainer"] { color: #252538 !important; }
        [data-testid="stMetric"] { background:#fff; border:4px ridge #d8d8d8; padding:14px; }
        [data-testid="stDataFrame"] {
            border:7px ridge #d8d8d8;
            background:#c0c0c0;
            padding:4px;
            box-shadow:6px 6px 0 #5454a8;
            margin:8px 0 24px;
        }
        [data-testid="stDataFrame"] button {
            background:#c0c0c0 !important;
            color:#111 !important;
            border:2px outset #fff !important;
            border-radius:0 !important;
        }
        [data-testid="stDataFrame"] button:active { border-style:inset !important; }
        [data-testid="stDataFrame"] [role="columnheader"] {
            font-family:"Courier New", monospace !important;
            font-weight:700 !important;
        }
        div[data-testid="stImage"] img { border:8px ridge #c0c0c0; box-shadow:8px 8px 0 #26266f; }
        [data-testid="stIFrame"] { border:7px ridge #d8d8d8; background:#c0c0c0; padding:6px; box-shadow:6px 6px 0 #5454a8; margin-bottom:20px; }
        .wordart-title {
            font-family: Impact, "Arial Black", sans-serif;
            font-size: clamp(2.7rem, 8vw, 6.7rem);
            line-height:.9;
            text-align:center;
            letter-spacing:-.06em;
            color:#41b8ff;
            background:linear-gradient(#baf2ff 5%,#48c7ff 35%,#0875d1 70%,#013273 100%);
            -webkit-background-clip:text;
            -webkit-text-fill-color:transparent;
            -webkit-text-stroke:2px #003886;
            filter:drop-shadow(8px 8px 0 #08206d);
            transform:skew(-5deg) rotate(-1deg);
            margin:28px 0 22px;
        }
        .retro-slogan { font-family:"Arial Black", Impact, sans-serif; font-size:clamp(1.8rem,4vw,3.6rem); line-height:1; color:#080808; transform:rotate(-3deg); margin:12px 0 25px; }
        .retro-orange { font-family:Impact, sans-serif; font-size:3.7rem; color:#ffb000; -webkit-text-stroke:1px #912800; text-shadow:4px 5px #a83b00; transform:rotate(4deg); display:inline-block; }
        .retro-purple { font-family:"Arial Black", sans-serif; font-size:2.6rem; color:#923cff; text-shadow:4px 4px #4b1e86; transform:skew(-9deg); display:inline-block; }
        .retro-outline { font-family:Arial, sans-serif; font-style:italic; font-size:2rem; color:white; -webkit-text-stroke:1px #111; text-shadow:2px 2px #ddd; }
        .marquee-box { overflow:hidden; border:5px ridge #ddd; background:#05056d; color:#fff900; font:bold 1.15rem "Courier New"; padding:8px; margin:12px 0 24px; white-space:nowrap; }
        .marquee-text { display:inline-block; animation:retro-scroll 14s linear infinite; }
        @keyframes retro-scroll { from { transform:translateX(100%); } to { transform:translateX(-100%); } }
        .blink { animation:blink 1s steps(2,start) infinite; }
        @keyframes blink { 50% { visibility:hidden; } }
        .retro-card { background:#fff; color:#111; border:5px ridge #d7d7d7; padding:16px; min-height:118px; box-shadow:5px 5px 0 #5454a8; margin-bottom:12px; }
        .visitor { font:700 .9rem "Courier New"; color:#fff; background:#000; border:3px inset #ddd; display:inline-block; padding:6px 10px; }
        @media (max-width:640px) {
            .wordart-title { font-size:3rem; filter:drop-shadow(4px 4px 0 #08206d); }
            .retro-slogan { font-size:2rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
