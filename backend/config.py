import os

from pathlib import Path

from dotenv import load_dotenv

_env_dir = Path(__file__).resolve().parent
load_dotenv(_env_dir / ".env.local", override=True)
load_dotenv(_env_dir / ".env", override=True)

APP_NAMESPACE = "substack_rec"

TWELVELABS_API_KEY = os.getenv("TWELVELABS_API_KEY", "")
TWELVELABS_INDEX_ID = os.getenv("TWELVELABS_INDEX_ID", "")
TWELVELABS_BASE_URL = "https://api.twelvelabs.io/v1.3"

CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

CREATOR_DESCRIPTIONS: dict[str, str] = {
    "UCPD_bxCRGpmmeQcbe2kpPaA": "Home of Hot Ones and the best food content on the internet.",
    "UC-b3c7kxa5vU-bnmaROgvog": "Business strategy, branding, and design education for creative professionals.",
    "UCamLstJyCa-t5gfZegxsFMw": "Exploring the creator economy through interviews and deep analysis of digital media.",
    "UCGq-a57w-aPwyi3pW7XLiHw": "Steven Bartlett hosts unfiltered conversations with the world's most influential people.",
    "UCmGSJVG3mCRXVOP4yZrU1Dw": "Visual storytelling that explains how borders, power, and money shape our world.",
    "UC4QZ_LsYcvcq7qOsOhpAX4A": "Exploring the stories behind technology, business, and the ideas shaping our future.",
    "UCLXo7UDZvByw2ixzpQCufnA": "Vox Earworm — the music that defines culture and why certain songs stick.",
    "UCDsElQQt_gCZ9LgnW-7v-cQ": "Fair Companies — self-sufficient living, tiny homes, and sustainable architecture worldwide.",
    "UCYO_jab_esuFRV4b17AJtAw": "Animated math — making complex ideas feel intuitive through visual storytelling.",
    "UCk2U-Oqn7RXf-ydPqfSxG5g": "Practical science-backed advice on motivation, habits, and personal transformation.",
    "UCBv7HEHuVlNAELGi5XJd85Q": "Exclusive artist interviews, live sessions, and music documentaries.",
}

ANALYZE_PROMPT = """Analyze this video and extract the following attributes. Return valid JSON only.

{
  "topic": ["topic1", "topic2", ...],
  "style": "one_of_enum",
  "tone": "one_of_enum"
}

style options (pick exactly one):
- "interview": one-on-one or panel conversation with a guest
- "documentary": narrative-driven visual storytelling, observational
- "essay": opinion-driven, first-person argument or reflection
- "tutorial": step-by-step instructional or how-to content
- "conversation": casual multi-person discussion, podcast-style
- "analysis": data-driven or research-backed breakdown of a topic
- "performance": music, comedy, art, or live performance
- "explainer": educational breakdown of a concept using visuals or animation

tone options (pick exactly one):
- "serious": formal, weighty subject matter, measured delivery
- "casual": relaxed, informal, conversational energy
- "playful": lighthearted, humorous, fun
- "contemplative": reflective, slow-paced, thought-provoking
- "energetic": fast-paced, enthusiastic, high energy
- "analytical": methodical, logic-driven, data-focused"""
