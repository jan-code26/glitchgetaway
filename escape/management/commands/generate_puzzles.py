"""
Management command to generate AI-powered escape room puzzles.

Usage:
    python manage.py generate_puzzles --topic "CSS" --count 5
    python manage.py generate_puzzles --prompt "Create puzzles about Python"
    python manage.py generate_puzzles --topic "JavaScript" --count 3 --provider anthropic
"""

from django.core.management.base import BaseCommand, CommandError
from escape.models import GeneratedPuzzle
from escape.ai_providers import get_provider


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

        # Build generation context for display
        if custom_prompt:
            context = f"custom prompt (generating {count} puzzle{'s' if count != 1 else ''})"
            generation_prompt = custom_prompt
        elif topic:
            context = f"topic: {topic} ({count} puzzle{'s' if count != 1 else ''})"
            generation_prompt = f"Topic: {topic}, Count: {count}"
        else:
            context = f"general tech/programming ({count} puzzle{'s' if count != 1 else ''})"
            generation_prompt = f"General tech/programming, Count: {count}"

        self.stdout.write(f"Generating puzzles with {context}...")

        # Get provider
        try:
            provider = get_provider(provider_name)
            provider_type = provider.__class__.__name__.replace('Provider', '')
            self.stdout.write(f"Using provider: {provider_type}")
        except ValueError as e:
            raise CommandError(str(e))
        except ImportError as e:
            raise CommandError(f"Provider dependency error: {e}")

        # Generate puzzles
        try:
            self.stdout.write("Calling AI API...")
            puzzles = provider.generate_puzzles(
                topic=topic,
                count=count,
                custom_prompt=custom_prompt
            )
        except Exception as e:
            raise CommandError(f"Failed to generate puzzles: {e}")

        if not puzzles:
            raise CommandError("No puzzles were generated")

        # Save to database
        self.stdout.write(f"Saving {len(puzzles)} puzzle{'s' if len(puzzles) != 1 else ''} to database...")
        created_count = 0
        
        for puzzle_data in puzzles:
            try:
                GeneratedPuzzle.objects.create(
                    title=puzzle_data['title'],
                    description=puzzle_data['description'],
                    puzzle_question=puzzle_data['puzzle_question'],
                    puzzle_answer=puzzle_data['puzzle_answer'],
                    alternate_answers=puzzle_data.get('alternate_answers', ''),
                    hint=puzzle_data.get('hint', 'No hint available.'),
                    generation_prompt=generation_prompt,
                    status=GeneratedPuzzle.STATUS_PENDING,
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Skipped invalid puzzle: {e}")
                )

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
