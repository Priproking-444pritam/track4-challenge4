# 🎙️ Spotify for Learning( https://track4-challenge4-luwvjfdzjevkeen2i3ltdj.streamlit.app/ )

**Turn any topic into a personalized podcast episode — solo narration or a full two-host conversation — powered by free AI.**

Type a topic. Groq writes a broadcast-ready script. gTTS narrates it. You get a playable, downloadable episode in seconds — in 15 languages.

---

## ✨ Features

- **AI script writing** via [Groq](https://groq.com) (free, fast LLM inference — `llama-3.3-70b-versatile`)
- **Free narration** via [gTTS](https://gtts.readthedocs.io) — no API key, no cost
- **🎙️🎙️ Two-host conversation mode** — a real back-and-forth dialogue between two hosts, not just one voice reading text
- **15 languages** — English, Hindi, Odia, Spanish, French, German, Japanese, Mandarin, Arabic, Portuguese, Russian, Korean, Italian, Bengali, Tamil
- **5 tone presets** — Educational, Storytelling, Casual & Fun, News Brief, Motivational
- **3 length presets** — Quick Bite (~2 min), Standard (~5 min), Deep Dive (~8 min)
- **Slower narration toggle** — handy for language learners
- **Downloadable MP3** for every episode
- **Session history** — replay or download anything you generated earlier
- A studio-style dark UI, not a default Streamlit page

---

## 🖥️ How It Works

```
Topic  ──▶  Groq (LLM)  ──▶  Script  ──▶  gTTS  ──▶  MP3  ──▶  Player + Download
```

- `backend/script_generator.py` — builds the prompt and calls Groq's chat completion API
- `backend/audio_generator.py` — converts the script to speech; in two-host mode, it synthesizes each line separately with a slightly different voice accent and stitches them together with `pydub`
- `main.py` — the Streamlit frontend and orchestration
- `config.py` — all languages, tones, lengths, and model settings in one place

---

## 🚀 Getting Started

### 1. Clone and install

```bash
git clone https://github.com/Priproking-444pritam/track4-challenge4.git
cd track4-challenge4
pip install -r requirements.txt
```

### 2. Get a free Groq API key

Sign up at **[console.groq.com/keys](https://console.groq.com/keys)** — no credit card needed — and copy your key.

You can either:
- Paste it directly into the sidebar when the app runs, **or**
- Copy `.env.example` to `.env` and add it there:
  ```bash
  cp .env.example .env
  # then edit .env and set GROQ_API_KEY=your_key_here
  ```

### 3. Run it

```bash
streamlit run main.py
```

Open the local URL Streamlit prints (usually `http://localhost:8501`).

> **Note on audio stitching:** two-host mode uses `pydub`, which needs `ffmpeg` installed on your system for best results (`sudo apt install ffmpeg` / `brew install ffmpeg`). If it's missing, the app automatically falls back to a single-voice narration instead of crashing.

---

## 🛠️ Tech Stack

| Layer      | Tool                                   |
|------------|-----------------------------------------|
| Frontend   | Streamlit + custom CSS                  |
| Script AI  | Groq API (`llama-3.3-70b-versatile`)    |
| Voice      | gTTS (Google Translate TTS)             |
| Audio glue | pydub                                   |

Both Groq and gTTS are free to use, so the whole project runs at zero cost.

---

## 🗺️ Roadmap Ideas

- [ ] Background music bed under narration
- [ ] Export as a shareable RSS/podcast feed
- [ ] Save episodes to disk instead of session-only history
- [ ] More than two hosts
- [ ] Voice speed/pitch controls per host

---

## 📄 License

No license specified yet — add one (MIT is a good default for a project like this) if you plan to share it publicly.
