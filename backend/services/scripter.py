"""
Gemini script generator — 6 styles.
Takes transcript → returns EN + Myanmar scripts.
"""
from google import genai
from backend.config import cfg

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=cfg.GEMINI_API_KEY)
    return _client

STYLE_PROMPTS = {
    "standard": "Write a clear, professional narration recap. Straightforward storytelling, informative tone.",
    "story":    "Write a compelling 3-act story recap: Setup → Conflict → Resolution. Hook the audience from the first line.",
    "quick":    "Write a punchy, fast-paced recap under 60 seconds. Short sentences. High energy. Get to the point fast.",
    "dramatic": "Write a dramatic, suspenseful recap. Build tension. Use emotional language. Leave the audience wanting more.",
    "comedy":   "Write a funny, lighthearted recap with humor and wit. Keep it entertaining and relatable.",
    "educational": "Write an informative, educational recap. Focus on key facts, lessons, and takeaways. Clear and structured.",
}

_PROMPT_TEMPLATE = """You are an expert viral content scriptwriter specializing in Myanmar social media.

Transcript:
{transcript}

Style: {style_desc}

Write a video recap script in BOTH English and Myanmar (Burmese).

Rules:
- Hook in the first sentence
- 200-300 words per language
- Conversational, natural tone
- No timestamps, no technical notes
- Copyright-safe: focus on themes and story, not verbatim quotes

Return ONLY valid JSON:
{{
  "english": "full english script here",
  "myanmar": "မြန်မာဘာသာ script ဒီမှာ"
}}"""


def generate_scripts(transcript: str, style: str = "standard") -> dict:
    style_desc = STYLE_PROMPTS.get(style, STYLE_PROMPTS["standard"])
    prompt = _PROMPT_TEMPLATE.format(
        transcript=transcript[:8000],
        style_desc=style_desc,
    )

    client = _get_client()
    response = client.models.generate_content(
        model=cfg.GEMINI_MODEL,
        contents=prompt,
    )
    raw = response.text.strip()

    # Strip markdown fences
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else parts[0]
        if raw.startswith("json"):
            raw = raw[4:]

    import json
    try:
        return json.loads(raw.strip())
    except Exception:
        # Fallback split
        return {
            "english": raw[:len(raw)//2].strip(),
            "myanmar": raw[len(raw)//2:].strip(),
        }
