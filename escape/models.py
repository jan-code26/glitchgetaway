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


class GeneratedPuzzle(models.Model):
    """AI-generated puzzle candidate awaiting review and approval."""
    
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    
    # Puzzle content (mirrors Room model fields)
    title = models.CharField(max_length=100)
    description = models.TextField()
    puzzle_question = models.TextField()
    puzzle_answer = models.CharField(max_length=100)
    alternate_answers = models.TextField(
        blank=True,
        default='',
        help_text="Comma-separated list of additional accepted answers.",
    )
    hint = models.TextField(blank=True, default="No hint available.")
    
    # Generation metadata
    generation_prompt = models.TextField(
        blank=True,
        help_text="The prompt or parameters used to generate this puzzle."
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    
    # Tracking fields
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_puzzles',
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Generated Puzzle"
        verbose_name_plural = "Generated Puzzles"
    
    def approve(self, user=None):
        """Create a Room from this puzzle and mark as approved."""
        if self.status == self.STATUS_APPROVED:
            # Already approved, return existing room
            return Room.objects.filter(
                title=self.title,
                puzzle_question=self.puzzle_question
            ).first()
        
        # Determine the next order value
        max_order = Room.objects.aggregate(models.Max('order'))['order__max'] or 0
        next_order = max_order + 1
        
        # Create the room
        room = Room.objects.create(
            order=next_order,
            title=self.title,
            description=self.description,
            puzzle_question=self.puzzle_question,
            puzzle_answer=self.puzzle_answer,
            alternate_answers=self.alternate_answers,
            hint=self.hint,
        )
        
        # Update this puzzle's status
        self.status = self.STATUS_APPROVED
        self.approved_at = timezone.now()
        self.approved_by = user
        self.save()
        
        return room
    
    def reject(self):
        """Mark this puzzle as rejected."""
        self.status = self.STATUS_REJECTED
        self.save()
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
