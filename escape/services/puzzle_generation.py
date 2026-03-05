"""Shared AI puzzle generation workflow for CLI and UI paths."""

from django.db import transaction

from escape.ai_providers import get_provider
from escape.models import GeneratedPuzzle, Room


def build_generation_context(topic=None, count=5, custom_prompt=None):
    """Build user-facing context text and stored generation prompt."""
    if custom_prompt:
        context = f"custom prompt (generating {count} puzzle{'s' if count != 1 else ''})"
        generation_prompt = custom_prompt
    elif topic:
        context = f"topic: {topic} ({count} puzzle{'s' if count != 1 else ''})"
        generation_prompt = f"Topic: {topic}, Count: {count}"
    else:
        context = f"general tech/programming ({count} puzzle{'s' if count != 1 else ''})"
        generation_prompt = f"General tech/programming, Count: {count}"

    return context, generation_prompt


def generate_and_store_puzzles(
    *,
    topic=None,
    count=5,
    custom_prompt=None,
    provider_name=None,
    auto_approve=False,
    approved_by=None,
):
    """Generate puzzles via AI provider, persist them, and optionally auto-approve."""
    if count < 1 or count > 20:
        raise ValueError("Count must be between 1 and 20")

    _, generation_prompt = build_generation_context(topic=topic, count=count, custom_prompt=custom_prompt)

    provider = get_provider(provider_name)
    provider_type = provider.__class__.__name__.replace("Provider", "")

    puzzles = provider.generate_puzzles(topic=topic, count=count, custom_prompt=custom_prompt)
    if not puzzles:
        raise ValueError("No puzzles were generated")

    created_count = 0
    approved_count = 0
    skipped_count = 0
    duplicate_skipped_count = 0
    errors = []

    for index, puzzle_data in enumerate(puzzles, start=1):
        if auto_approve and Room.objects.filter(
            title=puzzle_data["title"],
            puzzle_question=puzzle_data["puzzle_question"],
        ).exists():
            skipped_count += 1
            duplicate_skipped_count += 1
            errors.append(
                f"Puzzle #{index}: duplicate live room exists for this title/question"
            )
            continue

        try:
            with transaction.atomic():
                generated = GeneratedPuzzle.objects.create(
                    title=puzzle_data["title"],
                    description=puzzle_data["description"],
                    puzzle_question=puzzle_data["puzzle_question"],
                    puzzle_answer=puzzle_data["puzzle_answer"],
                    alternate_answers=puzzle_data.get("alternate_answers", ""),
                    hint=puzzle_data.get("hint", "No hint available."),
                    generation_prompt=generation_prompt,
                    status=GeneratedPuzzle.STATUS_PENDING,
                )
                created_count += 1

                if auto_approve:
                    generated.approve(user=approved_by)
                    approved_count += 1
        except Exception as exc:
            skipped_count += 1
            errors.append(f"Puzzle #{index}: {exc}")

    return {
        "provider_type": provider_type,
        "generated_count": len(puzzles),
        "created_count": created_count,
        "approved_count": approved_count,
        "skipped_count": skipped_count,
        "duplicate_skipped_count": duplicate_skipped_count,
        "errors": errors,
    }
