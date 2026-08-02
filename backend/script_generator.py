"""
Script generation backend, powered by Groq's free LLM API.

Groq is used because it is free to sign up for, extremely fast
(LPU inference), and has an OpenAI-compatible-ish Python SDK.
Get a free key at: https://console.groq.com/keys
"""

from groq import Groq
from config import GROQ_MODEL


class ScriptGenerationError(Exception):
    """Raised when Groq fails to return a usable script."""
    pass


def _client(api_key: str) -> Groq:
    if not api_key:
        raise ScriptGenerationError(
            "No Groq API key found. Add one in the sidebar or set GROQ_API_KEY."
        )
    return Groq(api_key=api_key)


def build_single_host_prompt(topic: str, language: str, tone_description: str, word_target: int) -> str:
    return f"""You are a professional podcast scriptwriter. Write a single-narrator podcast
episode script about: "{topic}"

Requirements:
- Write ENTIRELY in {language}.
- Tone/style: {tone_description}.
- Target length: approximately {word_target} words (this controls episode duration, so respect it).
- Structure: a short hook to open, 2-4 clear content segments, and a warm sign-off.
- Write it exactly as it should be SPOKEN ALOUD: natural sentences, contractions, no bullet points,
  no headers, no stage directions, no emojis, no markdown.
- Do not include any preamble like "Here is the script" — output ONLY the spoken script text.
"""


def build_two_host_prompt(topic: str, language: str, tone_description: str, word_target: int) -> str:
    return f"""You are a professional podcast scriptwriter. Write a TWO-HOST conversational podcast
episode script about: "{topic}"

Requirements:
- Write ENTIRELY in {language}.
- Tone/style: {tone_description}.
- Target length: approximately {word_target} words total (this controls episode duration, so respect it).
- Two hosts named exactly "Host A" and "Host B" who riff off each other naturally: asking
  questions, reacting, adding examples, occasionally disagreeing a little before agreeing.
- Structure: a short hook to open, 2-4 clear content segments as back-and-forth dialogue,
  and a warm sign-off from both hosts.
- Format EVERY line strictly as:
Host A: <line>
Host B: <line>
  (one speaker per line, nothing else on the line, no asterisks, no stage directions, no emojis)
- Do not include any preamble like "Here is the script" — output ONLY the formatted dialogue.
"""


def generate_script(
    api_key: str,
    topic: str,
    language: str,
    tone_description: str,
    word_target: int,
    two_host: bool = False,
) -> str:
    """
    Calls Groq's chat completion endpoint to write a podcast script.
    Returns the raw script text (plain text, or "Host A: / Host B:" formatted
    if two_host=True).
    """
    client = _client(api_key)

    prompt = (
        build_two_host_prompt(topic, language, tone_description, word_target)
        if two_host
        else build_single_host_prompt(topic, language, tone_description, word_target)
    )

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You write natural, engaging, broadcast-ready podcast scripts."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=2048,
        )
    except Exception as exc:  # noqa: BLE001 - surface a friendly message to the UI
        raise ScriptGenerationError(f"Groq request failed: {exc}") from exc

    script = response.choices[0].message.content.strip()

    if not script:
        raise ScriptGenerationError("Groq returned an empty script. Try again or rephrase the topic.")

    return script


def parse_two_host_script(script: str) -> list[tuple[str, str]]:
    """
    Parses a "Host A: ... / Host B: ..." script into an ordered list of
    (speaker, line) tuples, skipping any malformed lines defensively.
    """
    turns: list[tuple[str, str]] = []
    for raw_line in script.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.lower().startswith("host a:"):
            turns.append(("A", line.split(":", 1)[1].strip()))
        elif line.lower().startswith("host b:"):
            turns.append(("B", line.split(":", 1)[1].strip()))
        else:
            # Fallback: attach stray lines to the previous speaker so we
            # never silently drop content the model generated.
            if turns:
                speaker, prev_text = turns[-1]
                turns[-1] = (speaker, f"{prev_text} {line}")
    return turns
