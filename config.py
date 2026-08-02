"""
Central configuration for Spotify for Learning.
Keeping constants here means main.py and the backend modules
never go out of sync on things like language codes or model names.
"""

# ---------------------------------------------------------------------------
# Groq model used for script generation.
# llama-3.3-70b-versatile is free on Groq's developer tier and fast enough
# for interactive use (a 5-minute script script generates in ~2-4 seconds).
# ---------------------------------------------------------------------------
GROQ_MODEL = "llama-3.3-70b-versatile"

# ---------------------------------------------------------------------------
# Languages: label shown in the UI -> (script language name, gTTS lang code)
# gTTS codes: https://gtts.readthedocs.io/en/latest/module.html#languages-gtts-lang
# ---------------------------------------------------------------------------
LANGUAGES = {
    "English": ("English", "en"),
    "Hindi": ("Hindi", "hi"),
    "Odia": ("Odia", "or"),
    "Spanish": ("Spanish", "es"),
    "French": ("French", "fr"),
    "German": ("German", "de"),
    "Japanese": ("Japanese", "ja"),
    "Mandarin Chinese": ("Mandarin Chinese", "zh-CN"),
    "Arabic": ("Arabic", "ar"),
    "Portuguese": ("Portuguese", "pt"),
    "Russian": ("Russian", "ru"),
    "Korean": ("Korean", "ko"),
    "Italian": ("Italian", "it"),
    "Bengali": ("Bengali", "bn"),
    "Tamil": ("Tamil", "ta"),
}

# ---------------------------------------------------------------------------
# Tone / style presets for the script writer.
# ---------------------------------------------------------------------------
TONES = {
    "Educational": "clear, structured, and informative, like a great teacher explaining a topic simply",
    "Storytelling": "narrative and engaging, weaving the topic into a story or journey",
    "Casual & Fun": "relaxed, witty, and conversational, like two friends chatting over coffee",
    "News Brief": "punchy, fast-paced, and to the point, like a radio news segment",
    "Motivational": "energetic, inspiring, and encouraging, like a motivational speaker",
}

# ---------------------------------------------------------------------------
# Target length presets -> approximate spoken word count.
# Average conversational speech is ~140-150 words per minute.
# ---------------------------------------------------------------------------
LENGTHS = {
    "Quick Bite (~2 min)": 280,
    "Standard (~5 min)": 700,
    "Deep Dive (~8 min)": 1100,
}

# Number of episodes a guest (not logged in) can generate before being
# asked to create a free account.
FREE_TRIAL_LIMIT = 3

# Voices used for two-host conversational mode.
# gTTS doesn't offer distinct voices, so we vary the Google Translate TLD
# (tld) to get a subtly different accent per host — a cheap but effective trick.
HOST_A_TLD = "com"       # Host A: standard voice
HOST_B_TLD = "co.uk"     # Host B: slightly different accent