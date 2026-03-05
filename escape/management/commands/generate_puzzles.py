"""
Management command to generate AI-powered escape room puzzles.

Usage:
    python manage.py generate_puzzles --topic "CSS" --count 5
    python manage.py generate_puzzles --prompt "Create puzzles about Python"
    python manage.py generate_puzzles --topic "JavaScript" --count 3 --provider anthropic
"""

from django.core.management.base import BaseCommand, CommandError
from escape.services.puzzle_generation import (
    build_generation_context,
    generate_and_store_puzzles,
)


class Command(BaseCommand):
    help = 'Generate AI-powered escape room puzzles for review'

    def add_arguments(self, parser):
        parser.add_argument(
            '--topic',
            type=str,
            help='Topic or theme for the puzzles (e.g., "CSS", "Python", "HTTP")',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of puzzles to generate (default: 5)',
        )
        parser.add_argument(
            '--prompt',
            type=str,
            help='Custom prompt to override default generation logic',
        )
        parser.add_argument(
            '--provider',
            type=str,
            choices=['anthropic', 'openai', 'gemini'],
            help='Override AI provider (default: auto-detect from API keys)',
        )

    def handle(self, *args, **options):
        topic = options.get('topic')
        count = options.get('count')
        custom_prompt = options.get('prompt')
        provider_name = options.get('provider')

        # Validate count
        if count < 1 or count > 20:
            raise CommandError('Count must be between 1 and 20')

        context, _ = build_generation_context(
            topic=topic,
            count=count,
            custom_prompt=custom_prompt,
        )

        self.stdout.write(f"Generating puzzles with {context}...")

        # Generate and save via shared service
        try:
            self.stdout.write("Calling AI API...")
            result = generate_and_store_puzzles(
                topic=topic,
                count=count,
                custom_prompt=custom_prompt,
                provider_name=provider_name,
                auto_approve=False,
            )
            self.stdout.write(f"Using provider: {result['provider_type']}")
            self.stdout.write(
                f"Saving {result['generated_count']} puzzle{'s' if result['generated_count'] != 1 else ''} to database..."
            )
        except (ValueError, ImportError) as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f"Failed to generate puzzles: {e}")

        created_count = result['created_count']
        for error in result['errors']:
            self.stdout.write(self.style.WARNING(f"Skipped invalid puzzle: {error}"))

        # Report results
        if created_count == 0:
            raise CommandError("No valid puzzles could be saved")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Successfully generated {created_count} puzzle{'s' if created_count != 1 else ''}!"
            )
        )
        self.stdout.write(
            f"\nReview them in Django admin:"
        )
        self.stdout.write(
            self.style.HTTP_INFO("  → /admin/escape/generatedpuzzle/")
        )
        self.stdout.write(
            f"\nApprove puzzles to add them to the live escape room.\n"
        )
