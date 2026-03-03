from django.shortcuts import render, redirect

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import DurationField, ExpressionWrapper, F
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone
import json

from .models import GameSession, Room


def _leaderboard_qs():
    """Completed GameSessions annotated with elapsed duration, ordered fastest first."""
    return (
        GameSession.objects
        .filter(completed=True)
        .annotate(elapsed=ExpressionWrapper(
            F('finished_at') - F('started_at'),
            output_field=DurationField(),
        ))
        .order_by('elapsed', 'total_attempts')
    )


def get_progress(request):
    room_id = request.session.get('current_room_id')
    total = Room.objects.count()
    current_room = Room.objects.filter(id=room_id).first()
    if current_room:
        solved = Room.objects.filter(order__lt=current_room.order).count()
    else:
        solved = 0
    bar = '█' * solved + '-' * (total - solved)
    return {'solved': solved, 'total': total, 'bar': bar}


def portfolio(request):
    """Serve the portfolio landing page"""
    return render(request, 'escape/portfolio.html')


def home(request):
    """Redirect to the game; creates a GameSession when a fresh game starts."""
    if 'current_room_id' not in request.session:
        first_room = Room.objects.first()
        if not first_room:
            return HttpResponse("No rooms available. Please contact administrator.", status=500)
        request.session['current_room_id'] = first_room.id
        request.session['attempts'] = {}
        display_name = request.user.username if request.user.is_authenticated else 'Anonymous'
        session_obj = GameSession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            display_name=display_name,
        )
        request.session['game_session_id'] = session_obj.id
    return redirect('room')


def health_check(request):
    return JsonResponse({"status": "ok"})


def room_view(request):
    room_id = request.session.get('current_room_id')
    room = Room.objects.filter(id=room_id).first()
    game_session = GameSession.objects.filter(id=request.session.get('game_session_id')).first()

    if not room:
        request.session.flush()
        return redirect('home')

    start_iso = game_session.started_at.isoformat() if game_session else ''

    def render_room(error=None):
        return render(request, 'escape/room.html', {
            'room': room,
            'error': error,
            'progress': get_progress(request),
            'game_session': game_session,
            'game_session_start_iso': start_iso,
        })

    if request.method == 'POST':
        answer = request.POST.get('answer', '').strip().lower()

        if answer.startswith("sudo login"):
            code = answer.split()[-1]
            if code == settings.ADMIN_PASSWORD:
                request.session['is_admin'] = True
                return redirect('admin_terminal')
            else:
                return render_room("[[ ACCESS DENIED ]] Invalid admin code.")

        room_id = room.id
        attempts = request.session.get('attempts', {})
        room_attempts = attempts.get(str(room_id), 0)

        if answer == 'hint':
            if room_attempts >= 3:
                return render_room(f"[[ SYSTEM HINT ]] {room.hint}")
            else:
                return render_room("[[ SYSTEM MESSAGE ]] Hint not available yet. Try solving first.")

        elif answer == 'help':
            return render_room("[[ COMMANDS ]] help, hint, clear, leaderboard")

        elif answer == 'clear':
            return render_room("")

        elif answer == 'leaderboard':
            return redirect('leaderboard')

        if room.is_answer_correct(answer):
            attempts.pop(str(room_id), None)
            request.session['attempts'] = attempts
            next_room = Room.objects.filter(order__gt=room.order).first()
            if next_room:
                request.session['current_room_id'] = next_room.id
                return redirect('room')
            else:
                return redirect('success')
        else:
            attempts[str(room_id)] = room_attempts + 1
            request.session['attempts'] = attempts
            if game_session:
                game_session.total_attempts += 1
                game_session.save(update_fields=['total_attempts'])
            return render_room("[[ SYSTEM ]] Incorrect. Try again.")

    return render_room()


def success_view(request):
    game_session_id = request.session.get('game_session_id')
    game_session = None
    rank = None
    if game_session_id:
        game_session = GameSession.objects.filter(id=game_session_id).first()
        if game_session and not game_session.completed:
            game_session.completed = True
            game_session.finished_at = timezone.now()
            game_session.save()
        if game_session and game_session.completed:
            current_elapsed = game_session.finished_at - game_session.started_at
            rank = _leaderboard_qs().filter(elapsed__lt=current_elapsed).count() + 1
    request.session.flush()
    return render(request, 'escape/success.html', {'game_session': game_session, 'rank': rank})


def leaderboard_view(request):
    top_runs = _leaderboard_qs()[:10]
    return render(request, 'escape/leaderboard.html', {'top_runs': top_runs})


# ── Auth views ────────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        if not username or not password:
            error = "[[ ERROR ]] Username and password are required."
        elif User.objects.filter(username=username).exists():
            error = "[[ ERROR ]] Username already taken. Choose another."
        else:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            return redirect('home')
    return render(request, 'escape/register.html', {'error': error})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            error = "[[ ERROR ]] Invalid credentials. Try again."
    return render(request, 'escape/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('portfolio')


# ── Admin views ───────────────────────────────────────────────────────────────

def admin_terminal(request):
    if not request.session.get('is_admin'):
        if request.method == 'POST' and request.POST.get('admin_code') == settings.ADMIN_PASSWORD:
            request.session['is_admin'] = True
            return redirect('admin_terminal')
        else:
            return render(request, 'escape/admin_login.html')

    output = ""
    if request.method == 'POST' and 'command' in request.POST:
        cmd = request.POST['command'].strip().lower()

        if cmd.startswith('add_room'):
            return redirect('admin_add_room')

        elif cmd == 'list_rooms':
            output = "\n".join([f"{r.id}. {r.title}" for r in Room.objects.all()])

        elif cmd.startswith('delete_room'):
            try:
                pk = int(cmd.split()[-1])
                Room.objects.filter(pk=pk).delete()
                output = f"Room {pk} deleted."
            except Exception:
                output = "Invalid room ID."

        elif cmd == 'upload_rooms':
            return redirect('admin_upload_rooms')

        elif cmd.startswith('generate_puzzles'):
            parts = cmd.split()
            count = 3
            if len(parts) > 1:
                try:
                    count = int(parts[-1])
                except ValueError:
                    output = "Usage: generate_puzzles [count]"
                    return render(request, 'escape/admin_terminal.html', {'output': output})
            try:
                from escape.services import generate_puzzles_from_ai
                from escape.models import GeneratedPuzzle
                puzzles = generate_puzzles_from_ai(count=count)
                GeneratedPuzzle.objects.bulk_create([GeneratedPuzzle(**p) for p in puzzles])
                output = (
                    f"Generated {len(puzzles)} puzzle(s). "
                    "Review and approve them in the Django admin: /django-admin/escape/generatedpuzzle/"
                )
            except Exception as e:
                output = f"[[ ERROR ]] {e}"

        elif cmd == 'logout':
            request.session['is_admin'] = False
            return redirect('home')

        else:
            output = "Unknown command. Try: list_rooms, add_room, delete_room <id>, upload_rooms, generate_puzzles [count], logout"

    return render(request, 'escape/admin_terminal.html', {'output': output})


def admin_add_room(request):
    if not request.session.get('is_admin'):
        return redirect('admin_terminal')

    if request.method == 'POST':
        Room.objects.create(
            order=int(request.POST.get('order', 0)),
            title=request.POST['title'],
            description=request.POST['description'],
            puzzle_question=request.POST['question'],
            puzzle_answer=request.POST['answer'],
            alternate_answers=request.POST.get('alternate_answers', ''),
            hint=request.POST['hint']
        )
        return redirect('admin_terminal')

    return render(request, 'escape/admin_add_room.html')


def admin_upload_rooms(request):
    if not request.session.get('is_admin'):
        return redirect('admin_terminal')

    if request.method == 'POST':
        raw_json = request.POST.get('room_data', '')
        try:
            data = json.loads(raw_json)
            new_rooms = [
                Room(
                    order=item.get('order', 0),
                    title=item['title'],
                    description=item['description'],
                    puzzle_question=item['puzzle_question'],
                    puzzle_answer=item['puzzle_answer'],
                    alternate_answers=item.get('alternate_answers', ''),
                    hint=item.get('hint', '')
                ) for item in data
            ]
            Room.objects.bulk_create(new_rooms)
            messages.success(request, f"Uploaded {len(new_rooms)} rooms successfully.")
            return redirect('admin_terminal')
        except Exception as e:
            messages.error(request, f"Upload failed: {e}")

    return render(request, 'escape/admin_upload_rooms.html')

