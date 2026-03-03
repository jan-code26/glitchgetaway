from django.conf import settings
from django.db import models
from django.utils import timezone


class Room(models.Model):
    order = models.PositiveIntegerField(default=0, help_text="Display order of this room (lowest first).")
    title = models.CharField(max_length=100)
    description = models.TextField()
    puzzle_question = models.TextField()
    puzzle_answer = models.CharField(max_length=100)
    alternate_answers = models.TextField(
        blank=True,
        default='',
        help_text="Comma-separated list of additional accepted answers (case-insensitive).",
    )
    hint = models.TextField(blank=True, default="No hint available.")

    class Meta:
        ordering = ['order', 'id']

    def is_answer_correct(self, answer):
        """Return True if *answer* matches the primary or any alternate answer."""
        answer = answer.strip().lower()
        if answer == self.puzzle_answer.strip().lower():
            return True
        if self.alternate_answers:
            alts = [a.strip().lower() for a in self.alternate_answers.split(',') if a.strip()]
            return answer in alts
        return False

    def __str__(self):
        return self.title


class GameSession(models.Model):
    """Tracks a single play-through, optionally linked to an authenticated user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='game_sessions',
    )
    display_name = models.CharField(max_length=50, default='Anonymous')
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    total_attempts = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['finished_at']

    @property
    def elapsed_seconds(self):
        if self.finished_at:
            return max(0, int((self.finished_at - self.started_at).total_seconds()))
        return None

    @property
    def elapsed_display(self):
        secs = self.elapsed_seconds
        if secs is None:
            return '--:--'
        return f"{secs // 60:02d}:{secs % 60:02d}"

    def __str__(self):
        status = 'completed' if self.completed else 'in progress'
        return f"{self.display_name} — {status}"
