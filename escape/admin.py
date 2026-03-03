from django.contrib import admin
from django.utils import timezone

from .models import GeneratedPuzzle, Room

admin.site.register(Room)


@admin.register(GeneratedPuzzle)
class GeneratedPuzzleAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'created_at', 'reviewed_at')
    list_filter = ('status',)
    readonly_fields = ('created_at', 'reviewed_at')
    actions = ['approve_puzzles', 'reject_puzzles']

    @admin.action(description='Approve selected puzzles and add them to the game')
    def approve_puzzles(self, request, queryset):
        approved_count = 0
        for gp in queryset.filter(status=GeneratedPuzzle.STATUS_PENDING):
            Room.objects.create(
                order=gp.order,
                title=gp.title,
                description=gp.description,
                puzzle_question=gp.puzzle_question,
                puzzle_answer=gp.puzzle_answer,
                alternate_answers=gp.alternate_answers,
                hint=gp.hint,
            )
            gp.status = GeneratedPuzzle.STATUS_APPROVED
            gp.reviewed_at = timezone.now()
            gp.save(update_fields=['status', 'reviewed_at'])
            approved_count += 1
        self.message_user(request, f'{approved_count} puzzle(s) approved and added to the game.')

    @admin.action(description='Reject selected puzzles')
    def reject_puzzles(self, request, queryset):
        rejected_count = queryset.filter(status=GeneratedPuzzle.STATUS_PENDING).update(
            status=GeneratedPuzzle.STATUS_REJECTED,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f'{rejected_count} puzzle(s) rejected.')

