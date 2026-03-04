from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import Room, GeneratedPuzzle, GameSession


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Enhanced admin for Room model."""
    
    list_display = ['order', 'title', 'question_preview', 'has_hint', 'has_alternates']
    list_display_links = ['title']
    list_editable = ['order']
    search_fields = ['title', 'description', 'puzzle_question']
    ordering = ['order', 'id']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('order', 'title', 'description')
        }),
        ('Puzzle', {
            'fields': ('puzzle_question', 'puzzle_answer', 'alternate_answers')
        }),
        ('Help', {
            'fields': ('hint',)
        }),
    )
    
    def question_preview(self, obj):
        """Show first 60 characters of the question."""
        q = obj.puzzle_question
        return q if len(q) <= 60 else f"{q[:57]}..."
    question_preview.short_description = "Question"
    
    def has_hint(self, obj):
        """Show if a custom hint is available."""
        has_custom = obj.hint and obj.hint != "No hint available."
        return "✓" if has_custom else "—"
    has_hint.short_description = "Hint"
    
    def has_alternates(self, obj):
        """Show if alternate answers exist."""
        return "✓" if obj.alternate_answers else "—"
    has_alternates.short_description = "Alt Answers"


@admin.register(GeneratedPuzzle)
class GeneratedPuzzleAdmin(admin.ModelAdmin):
    """Enhanced admin for AI-generated puzzle review and approval."""
    
    list_display = [
        'status_icon',
        'title',
        'question_preview',
        'created_at',
        'approved_info'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'puzzle_question', 'description']
    ordering = ['-created_at']
    actions = ['approve_selected', 'reject_selected']
    
    fieldsets = (
        ('Status', {
            'fields': ('status', 'created_at', 'approved_at', 'approved_by')
        }),
        ('Puzzle Content', {
            'fields': ('title', 'description', 'puzzle_question', 'puzzle_answer', 'alternate_answers', 'hint')
        }),
        ('Generation Info', {
            'fields': ('generation_prompt',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'approved_at', 'approved_by']
    
    def get_readonly_fields(self, request, obj=None):
        """Make fields readonly for approved puzzles."""
        readonly = list(self.readonly_fields)
        if obj and obj.status == GeneratedPuzzle.STATUS_APPROVED:
            # Lock content for approved puzzles
            readonly.extend([
                'title', 'description', 'puzzle_question',
                'puzzle_answer', 'alternate_answers', 'hint',
                'generation_prompt', 'status'
            ])
        return readonly
    
    def status_icon(self, obj):
        """Show status with colored icon."""
        icons = {
            GeneratedPuzzle.STATUS_PENDING: '⏳',
            GeneratedPuzzle.STATUS_APPROVED: '✅',
            GeneratedPuzzle.STATUS_REJECTED: '❌',
        }
        colors = {
            GeneratedPuzzle.STATUS_PENDING: '#ff9800',
            GeneratedPuzzle.STATUS_APPROVED: '#4caf50',
            GeneratedPuzzle.STATUS_REJECTED: '#f44336',
        }
        icon = icons.get(obj.status, '?')
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="font-size: 16px; color: {};">{}</span>',
            color, icon
        )
    status_icon.short_description = "Status"
    
    def question_preview(self, obj):
        """Show first 80 characters of the question."""
        q = obj.puzzle_question
        return q if len(q) <= 80 else f"{q[:77]}..."
    question_preview.short_description = "Question"
    
    def approved_info(self, obj):
        """Show approval information."""
        if obj.status == GeneratedPuzzle.STATUS_APPROVED:
            if obj.approved_by:
                return f"by {obj.approved_by.username}"
            return "approved"
        return "—"
    approved_info.short_description = "Approved"
    
    def approve_selected(self, request, queryset):
        """Bulk approve selected puzzles."""
        pending = queryset.filter(status=GeneratedPuzzle.STATUS_PENDING)
        count = 0
        
        for puzzle in pending:
            try:
                puzzle.approve(user=request.user)
                count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"Failed to approve '{puzzle.title}': {e}",
                    level='ERROR'
                )
        
        if count > 0:
            self.message_user(
                request,
                f"Successfully approved {count} puzzle{'s' if count != 1 else ''} and created Room entries.",
                level='SUCCESS'
            )
    approve_selected.short_description = "✓ Approve selected puzzles"
    
    def reject_selected(self, request, queryset):
        """Bulk reject selected puzzles."""
        pending = queryset.filter(status=GeneratedPuzzle.STATUS_PENDING)
        count = pending.count()
        
        for puzzle in pending:
            puzzle.reject()
        
        if count > 0:
            self.message_user(
                request,
                f"Rejected {count} puzzle{'s' if count != 1 else ''}.",
                level='WARNING'
            )
    reject_selected.short_description = "✗ Reject selected puzzles"


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    """Admin for game sessions (view only)."""
    
    list_display = ['display_name', 'completed', 'elapsed_display', 'started_at', 'total_attempts']
    list_filter = ['completed', 'started_at']
    search_fields = ['display_name', 'user__username']
    ordering = ['-started_at']
    
    # Make read-only
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
