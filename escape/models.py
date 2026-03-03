from django.db import models


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
