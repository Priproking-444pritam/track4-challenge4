"""
Spotify for Learning — AI Podcast Studio
------------------------------------------------
Type a topic -> Groq writes a podcast script -> gTTS narrates it -> you listen.

Backend:  Groq (free LLM API) for script generation
Voice:    gTTS (free, no key required) for text-to-speech
Accounts: MongoDB for login + saved episode history
Frontend: Streamlit, with a custom "on-air studio" theme
"""

import os
import datetime as dt

import streamlit as st
from dotenv import load_dotenv

from config import LANGUAGES, TONES, LENGTHS, FREE_TRIAL_LIMIT
from backend.script_generator import generate_script, parse_two_host_script, ScriptGenerationError
from backend.audio_generator import synthesize_single, synthesize_two_host, AudioGenerationError
from backend import auth

load_dotenv()

st.set_page_config(
    page_title="Waveform Studio — AI Podcasts",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_groq_api_key() -> str | None:
    """
    The Groq key lives on the server only — in a local .env file, or in
    Streamlit's secrets.toml when deployed. It is never entered or shown
    in the UI, so end users never see or touch it.
    """
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("GROQ_API_KEY")
    except Exception:
        return None


GROQ_API_KEY = get_groq_api_key()

# ---------------------------------------------------------------------------
# Theme: dark "on-air studio" look with a slow-drifting green mesh
# background (a nod to Spotify's own gradient language), amber/coral accents
# for the AI + two-host details, Space Grotesk display type, IBM Plex Sans
# body copy, JetBrains Mono for timestamps/labels.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --ink: #0B0F0D;
    --panel: #141A16;
    --panel-border: #23302A;
    --spotify-green: #1DB954;
    --green-deep: #0F5A2E;
    --amber: #F2A93B;
    --amber-dim: #8a6a2c;
    --coral: #E85D75;
    --text: #F2EFE6;
    --muted: #8A9490;
}

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

/* ---- Animated green mesh background ---- */
.stApp {
    background: var(--ink);
    color: var(--text);
    position: relative;
    overflow-x: hidden;
}
.bg-blobs { position: fixed; inset: 0; z-index: -1; overflow: hidden; pointer-events: none; }
.bg-blobs i {
    position: absolute; border-radius: 50%; filter: blur(90px); opacity: 0.35;
    background: radial-gradient(circle at 30% 30%, var(--spotify-green), var(--green-deep) 70%);
    animation: drift 22s ease-in-out infinite;
}
.bg-blobs i:nth-child(1) { width: 520px; height: 520px; top: -180px; left: -120px; animation-duration: 26s; }
.bg-blobs i:nth-child(2) { width: 420px; height: 420px; top: 40%; right: -160px; animation-duration: 20s; animation-delay: -6s; opacity: 0.28; }
.bg-blobs i:nth-child(3) { width: 380px; height: 380px; bottom: -160px; left: 20%; animation-duration: 24s; animation-delay: -12s; opacity: 0.22; }
@keyframes drift {
    0%   { transform: translate(0, 0) scale(1); }
    33%  { transform: translate(60px, 40px) scale(1.08); }
    66%  { transform: translate(-40px, -30px) scale(0.95); }
    100% { transform: translate(0, 0) scale(1); }
}
[data-testid="stAppViewContainer"], section[data-testid="stSidebar"] { position: relative; z-index: 1; }
[data-testid="stHeader"] { background: transparent; }

section[data-testid="stSidebar"] { background: rgba(11,15,13,0.88); border-right: 1px solid var(--panel-border); backdrop-filter: blur(6px); }

h1, h2, h3, .display-font { font-family: 'Space Grotesk', sans-serif; }
.mono { font-family: 'JetBrains Mono', monospace; }

/* ---- Hero ---- */
.hero-wrap { padding: 1.6rem 0 1.2rem 0; border-bottom: 1px solid var(--panel-border); margin-bottom: 1.6rem; }
.on-air-tag {
    font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 0.18em;
    color: var(--spotify-green); border: 1px solid #1c5c33; border-radius: 999px;
    padding: 0.22rem 0.7rem; display: inline-flex; align-items: center; gap: 0.4rem;
}
.on-air-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--coral);
    box-shadow: 0 0 8px var(--coral); animation: pulse 1.6s ease-in-out infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }

.hero-title { font-size: 2.6rem; font-weight: 700; margin: 0.55rem 0 0.3rem 0; line-height: 1.08; color: var(--text); }
.hero-title span { color: var(--spotify-green); }
.hero-sub { color: var(--muted); font-size: 1.02rem; max-width: 640px; }

/* ---- Waveform signature ---- */
.wave { display: flex; align-items: flex-end; gap: 4px; height: 46px; margin: 1.1rem 0 0.2rem 0; }
.wave i { display: block; width: 4px; border-radius: 3px; background: linear-gradient(180deg, var(--spotify-green), var(--amber));
    animation: bar 1.2s ease-in-out infinite; }
@keyframes bar { 0%,100% { transform: scaleY(0.25); } 50% { transform: scaleY(1); } }

/* ---- Cards ---- */
.panel { background: var(--panel); border: 1px solid var(--panel-border); border-radius: 14px; padding: 1.3rem 1.4rem; }
.eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; letter-spacing: 0.14em; color: var(--muted); text-transform: uppercase; }

/* ---- Buttons ---- */
.stButton > button {
    background: linear-gradient(135deg, var(--spotify-green), #14893f); color: #06170C; border: none;
    font-weight: 600; border-radius: 10px; padding: 0.6rem 1.4rem; font-family: 'Space Grotesk', sans-serif;
    transition: transform 0.12s ease, box-shadow 0.12s ease;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(29,185,84,0.28); }

.stDownloadButton > button {
    background: transparent; color: var(--spotify-green); border: 1px solid #1c5c33; border-radius: 10px; font-family: 'Space Grotesk', sans-serif;
}

/* ---- History cards ---- */
.history-card { background: var(--panel); border: 1px solid var(--panel-border); border-radius: 12px; padding: 0.9rem 1.1rem; margin-bottom: 0.7rem; }
.history-topic { font-weight: 600; color: var(--text); font-family: 'Space Grotesk', sans-serif; }
.history-meta { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--muted); }

.host-a-line { color: var(--spotify-green); font-weight: 600; }
.host-b-line { color: var(--coral); font-weight: 600; }

.trial-pill {
    font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--muted);
    border: 1px dashed var(--panel-border); border-radius: 10px; padding: 0.5rem 0.7rem; margin-top: 0.4rem;
}

footer, #MainMenu { visibility: hidden; }

/* ---- Fix: input/textarea boxes are white regardless of dark theme,
   so force dark, readable text inside them instead of inheriting the
   pale --text color meant for the dark background. ---- */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
    color: #1A1D1A !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
    color: #6B6F6C !important;
}

</style>

<div class="bg-blobs"><i></i><i></i><i></i></div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "current" not in st.session_state:
    st.session_state.current = None
if "user" not in st.session_state:
    st.session_state.user = None
if "trial_count" not in st.session_state:
    st.session_state.trial_count = 0

accounts_available = auth.is_configured()


# ---------------------------------------------------------------------------
# Sidebar — account + studio controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<p class="eyebrow">Studio Access</p>', unsafe_allow_html=True)

    if st.session_state.user:
        st.markdown(f"### 👋 {st.session_state.user}")
        st.caption("Signed in — your episodes are saved to your account.")
        if st.button("Log out", use_container_width=True):
            st.session_state.user = None
            st.session_state.history = []
            st.session_state.current = None
            st.rerun()

    elif not accounts_available:
        st.markdown("### 🎧 Free Trial")
        remaining = max(0, FREE_TRIAL_LIMIT - st.session_state.trial_count)
        st.markdown(
            f'<div class="trial-pill">{remaining} of {FREE_TRIAL_LIMIT} free episodes left this session</div>',
            unsafe_allow_html=True,
        )
        st.caption("Accounts aren't configured on this deployment yet, so everyone uses the free trial.")

    else:
        tab_login, tab_signup, tab_guest = st.tabs(["Log in", "Sign up", "Guest"])

        with tab_login:
            with st.form("login_form"):
                lu = st.text_input("Username", key="login_user")
                lp = st.text_input("Password", type="password", key="login_pass")
                if st.form_submit_button("Log in", use_container_width=True):
                    try:
                        username = auth.login(lu, lp)
                        st.session_state.user = username
                        st.session_state.history = auth.get_episodes(username)
                        st.session_state.current = None
                        st.rerun()
                    except auth.AuthError as e:
                        st.error(str(e))

        with tab_signup:
            with st.form("signup_form"):
                su = st.text_input("Choose a username", key="signup_user")
                sp = st.text_input("Choose a password", type="password", key="signup_pass")
                if st.form_submit_button("Create account", use_container_width=True):
                    try:
                        auth.signup(su, sp)
                        st.success("Account created! Switch to the Log in tab.")
                    except auth.AuthError as e:
                        st.error(str(e))

        with tab_guest:
            remaining = max(0, FREE_TRIAL_LIMIT - st.session_state.trial_count)
            st.markdown(
                f'<div class="trial-pill">{remaining} of {FREE_TRIAL_LIMIT} free episodes left this session</div>',
                unsafe_allow_html=True,
            )
            st.caption("Sign up any time to save your episodes and get unlimited generations.")

    st.divider()
    st.markdown('<p class="eyebrow">Studio Controls</p>', unsafe_allow_html=True)
    st.markdown("### 🎛️ Settings")

    language_label = st.selectbox("Language", list(LANGUAGES.keys()), index=0)
    tone_label = st.selectbox("Tone", list(TONES.keys()), index=0)
    length_label = st.selectbox("Length", list(LENGTHS.keys()), index=1)

    two_host = st.toggle("🎙️🎙️ Two-host conversation mode", value=False,
                          help="Generates a back-and-forth dialogue between two hosts instead of one narrator.")
    slow_voice = st.toggle("🐢 Slower narration", value=False, help="Useful for language learning.")

    st.divider()
    st.caption(f"Episodes generated this session: **{len(st.session_state.history)}**")


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="hero-wrap">
    <span class="on-air-tag"><span class="on-air-dot"></span> ON AIR · AI GENERATED</span>
    <div class="hero-title">Spotify for Learning<br><span>Turn any topic into a podcast.</span></div>
    <div class="hero-sub">Type what you want to learn. Groq writes the script, gTTS narrates it,
    and you get a ready-to-play episode — in {len(LANGUAGES)} languages, solo or two-host style.</div>
    <div class="wave">
        {''.join(f'<i style="height:{h}px;animation-delay:{d}s;"></i>' for h, d in zip([14,28,40,20,34,16,30,44,22,12,26,38,18,32,10], [0.0,0.08,0.16,0.24,0.32,0.4,0.48,0.56,0.64,0.72,0.8,0.88,0.96,1.04,1.12]))}
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main input panel
# ---------------------------------------------------------------------------
left, right = st.columns([1.35, 1])

trial_exhausted = (
    not st.session_state.user
    and st.session_state.trial_count >= FREE_TRIAL_LIMIT
)

with left:
    st.markdown('<p class="eyebrow">01 · Topic</p>', unsafe_allow_html=True)
    topic = st.text_area(
        "What should this episode be about?",
        placeholder="e.g. Why black holes don't actually 'suck' things in, explained simply",
        height=110,
        label_visibility="collapsed",
        disabled=trial_exhausted,
    )

    if trial_exhausted:
        st.warning("You've used all your free episodes. Create a free account in the sidebar to keep going — "
                    "unlimited episodes and your history saved.")
        generate_clicked = False
    else:
        generate_clicked = st.button("▶ Generate Episode", use_container_width=True, type="primary")

    if generate_clicked:
        if not GROQ_API_KEY:
            st.error("This deployment isn't configured with a Groq API key yet. "
                     "Add GROQ_API_KEY to your .env file or Streamlit secrets.")
        elif not topic.strip():
            st.error("Give the episode a topic to talk about.")
        else:
            script_lang, tts_lang = LANGUAGES[language_label]
            tone_desc = TONES[tone_label]
            word_target = LENGTHS[length_label]

            try:
                with st.spinner("✍️ Writing your script with Groq..."):
                    script = generate_script(
                        api_key=GROQ_API_KEY,
                        topic=topic.strip(),
                        language=script_lang,
                        tone_description=tone_desc,
                        word_target=word_target,
                        two_host=two_host,
                    )

                with st.spinner("🔊 Recording narration with gTTS..."):
                    if two_host:
                        turns = parse_two_host_script(script)
                        audio_bytes = synthesize_two_host(turns, tts_lang, slow=slow_voice)
                    else:
                        audio_bytes = synthesize_single(script, tts_lang, slow=slow_voice)

                entry = {
                    "topic": topic.strip(),
                    "language": language_label,
                    "tone": tone_label,
                    "length": length_label,
                    "two_host": two_host,
                    "script": script,
                    "audio": audio_bytes,
                    "timestamp": dt.datetime.now().strftime("%H:%M:%S"),
                }
                st.session_state.current = entry
                st.session_state.history.insert(0, entry)

                if st.session_state.user:
                    auth.save_episode(st.session_state.user, entry)
                else:
                    st.session_state.trial_count += 1

                st.toast("Episode ready 🎧", icon="✅")

            except ScriptGenerationError as e:
                st.error(f"Script generation failed: {e}")
            except AudioGenerationError as e:
                st.error(f"Narration failed: {e}")

with right:
    st.markdown('<p class="eyebrow">Quick Guide</p>', unsafe_allow_html=True)
    st.markdown("""
    <div class="panel">
    <b>1.</b> Pick a language, tone and length<br><br>
    <b>2.</b> Try <b>two-host mode</b> for a real back-and-forth conversation<br><br>
    <b>3.</b> Hit generate, then play or download the MP3<br><br>
    <b>4.</b> Create a free account to save your history across visits
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Current episode output
# ---------------------------------------------------------------------------
current = st.session_state.current
if current:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="eyebrow">02 · Your Episode</p>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="panel">
        <div class="history-topic" style="font-size:1.15rem;">{current['topic']}</div>
        <div class="history-meta">{current['language']} · {current['tone']} · {current['length']}
        {'· 🎙️🎙️ two-host' if current['two_host'] else '· 🎙️ single narrator'} · generated {current['timestamp']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.audio(current["audio"], format="audio/mp3")

    dl_col, sc_col = st.columns([1, 1])
    with dl_col:
        st.download_button(
            "⬇ Download MP3",
            data=current["audio"],
            file_name=f"{current['topic'][:40].strip().replace(' ', '_')}.mp3",
            mime="audio/mpeg",
            use_container_width=True,
        )

    with st.expander("📜 View script"):
        if current["two_host"]:
            for speaker, line in parse_two_host_script(current["script"]):
                css_class = "host-a-line" if speaker == "A" else "host-b-line"
                st.markdown(f'<span class="{css_class}">Host {speaker}:</span> {line}', unsafe_allow_html=True)
        else:
            st.write(current["script"])


# ---------------------------------------------------------------------------
# History (session-only for guests, persisted across visits for logged-in users)
# ---------------------------------------------------------------------------
if len(st.session_state.history) > 1:
    st.markdown("<br>", unsafe_allow_html=True)
    label = "Your Saved Episodes" if st.session_state.user else "Previous Episodes This Session"
    st.markdown(f'<p class="eyebrow">{label}</p>', unsafe_allow_html=True)

    for i, item in enumerate(st.session_state.history[1:], start=1):
        st.markdown(f"""
        <div class="history-card">
            <div class="history-topic">{item['topic']}</div>
            <div class="history-meta">{item['language']} · {item['tone']} · {item['timestamp']}</div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander(f"Play — {item['topic'][:50]}", expanded=False):
            st.audio(item["audio"], format="audio/mp3")
            st.download_button(
                "⬇ Download MP3",
                data=item["audio"],
                file_name=f"{item['topic'][:40].strip().replace(' ', '_')}.mp3",
                mime="audio/mpeg",
                key=f"dl_{i}",
            )

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    '<p class="mono" style="color:#4a4d5e; font-size:0.75rem;">Spotify for Learning · Groq + gTTS + MongoDB · built for Track 4</p>',
    unsafe_allow_html=True,
)