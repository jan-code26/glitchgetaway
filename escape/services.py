"""Services for AI-powered puzzle generation using the Anthropic API."""

import json
import logging

from django.conf import settings

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

PUZZLE_GENERATION_PROMPT = """You are a puzzle designer for a hacker-themed terminal escape room game.
Generate {count} unique, creative puzzles that fit the hacker/terminal aesthetic.

Each puzzle must be a freeform terminal-input question where the player types a short answer
(a single word, number, or short phrase).  Good topics include:
- Python or JavaScript code snippets ("what does this print?")
- Unix/Linux command trivia ("which command lists directory contents?")
- Networking or security concepts
- Programming terminology

Return a JSON array (no markdown, no extra text) with exactly {count} objects.
Each object must have these keys:
  "order"             – integer (suggested display order, starting at 1)
  "title"             – short room title (max 60 chars)
  "description"       – 1-2 sentence flavour text with hacker/terminal theme
  "puzzle_question"   – the question shown to the player
  "puzzle_answer"     – the single correct answer (lowercase, no spaces where possible)
  "alternate_answers" – comma-separated alternate accepted answers, or empty string
  "hint"              – a subtle hint revealed after 3 wrong attempts

Make each puzzle distinct and progressively more challenging.
"""


def generate_puzzles_from_ai(count: int = 3) -> list[dict]:
    """
    Call the Anthropic API and return a list of puzzle dicts ready to be saved
    as ``GeneratedPuzzle`` instances.

    Raises ``RuntimeError`` if the API key is missing or the response cannot
    be parsed as a valid puzzle list.
    """
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not configured.  Set it via the environment variable."
        )

    if anthropic is None:
        raise RuntimeError("The 'anthropic' package is not installed.")

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": PUZZLE_GENERATION_PROMPT.format(count=count),
            }
        ],
    )

    raw_text = message.content[0].text.strip()

    try:
        puzzles = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.error("Anthropic returned non-JSON content: %s", raw_text[:500])
        raise RuntimeError(f"AI response could not be parsed as JSON: {exc}") from exc

    if not isinstance(puzzles, list):
        raise RuntimeError("AI response is not a JSON array.")

    required_keys = {"title", "description", "puzzle_question", "puzzle_answer"}
    validated = []
    for idx, item in enumerate(puzzles):
        missing = required_keys - item.keys()
        if missing:
            raise RuntimeError(f"Puzzle {idx} is missing keys: {missing}")
        validated.append({
            "order": int(item.get("order", 0)),
            "title": str(item["title"])[:100],
            "description": str(item["description"]),
            "puzzle_question": str(item["puzzle_question"]),
            "puzzle_answer": str(item["puzzle_answer"])[:100],
            "alternate_answers": str(item.get("alternate_answers", "")),
            "hint": str(item.get("hint", "No hint available.")),
        })

    return validated
