"""Management command: generate AI puzzles and save them for admin review."""

from django.core.management.base import BaseCommand, CommandError

from escape.models import GeneratedPuzzle
from escape.services import generate_puzzles_from_ai


class Command(BaseCommand):
    help = (
        "Generate puzzles using the Anthropic API and save them as pending "
        "GeneratedPuzzle records for review in the Django admin."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=3,
            help="Number of puzzles to generate (default: 3).",
        )

    def handle(self, *args, **options):
        count = options["count"]
        self.stdout.write(f"Requesting {count} puzzle(s) from the Anthropic API…")

        try:
            puzzles = generate_puzzles_from_ai(count=count)
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc

        created = GeneratedPuzzle.objects.bulk_create(
            [GeneratedPuzzle(**puzzle) for puzzle in puzzles]
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(created)} GeneratedPuzzle record(s) with status=pending. "
                "Review and approve them in the Django admin at /django-admin/escape/generatedpuzzle/."
            )
        )
