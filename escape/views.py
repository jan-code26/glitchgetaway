from django.shortcuts import render, redirect

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
import json

from .models import Room


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
    """Redirect to the game (kept for backwards compatibility)"""
    if 'current_room_id' not in request.session:
        first_room = Room.objects.first()
        if not first_room:
            return HttpResponse("No rooms available. Please contact administrator.", status=500)
        request.session['current_room_id'] = first_room.id
    return redirect('room')


def health_check(request):
    return JsonResponse({"status": "ok"})


def room_view(request):
    room_id = request.session.get('current_room_id')
    room = Room.objects.filter(id=room_id).first()

    if not room:
        request.session.flush()
        return redirect('home')

    error = None
    if request.method == 'POST':
        answer = request.POST.get('answer', '').strip().lower()
        if answer.startswith("sudo login"):
            code = answer.split()[-1]
            if code == settings.ADMIN_PASSWORD:
                request.session['is_admin'] = True
                return redirect('admin_terminal')
            else:
                error = "[[ ACCESS DENIED ]] Invalid admin code."
        room_id = room.id

        # Initialize attempts tracker
        attempts = request.session.get('attempts', {})
        room_attempts = attempts.get(str(room_id), 0)

        # Handle terminal commands
        if answer == 'hint':
            if room_attempts >= 3:
                error = f"[[ SYSTEM HINT ]] {room.hint}"
            else:
                error = "[[ SYSTEM MESSAGE ]] Hint not available yet. Try solving first."
            return render(request, 'escape/room.html', {'room': room, 'error': error, 'progress': get_progress(request)})

        elif answer == 'help':
            error = "[[ COMMANDS ]] help, hint, clear"
            return render(request, 'escape/room.html', {'room': room, 'error': error, 'progress': get_progress(request)})

        elif answer == 'clear':
            error = ""  # empty error clears screen effect
            return render(request, 'escape/room.html', {'room': room, 'error': error, 'progress': get_progress(request)})

        # Check if answer is correct (primary + alternate answers)
        if room.is_answer_correct(answer):
            # Clear attempts on success
            attempts.pop(str(room_id), None)
            request.session['attempts'] = attempts

            next_room = Room.objects.filter(order__gt=room.order).first()
            if next_room:
                request.session['current_room_id'] = next_room.id
                return redirect('room')
            else:
                return redirect('success')
        else:
            # Increase attempt count
            attempts[str(room_id)] = room_attempts + 1
            request.session['attempts'] = attempts
            error = "[[ SYSTEM ]] Incorrect. Try again."

        return render(request, 'escape/room.html', {'room': room, 'error': error, 'progress': get_progress(request)})

    return render(request, 'escape/room.html', {
        'room': room,
        'error': error,
        'progress': get_progress(request),
    })


def success_view(request):
    request.session.flush()
    return render(request, 'escape/success.html')


# Admin terminal entry point
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

        elif cmd == 'logout':
            request.session['is_admin'] = False
            return redirect('home')

        else:
            output = "Unknown command. Try: list_rooms, add_room, delete_room <id>, upload_rooms, logout"

    return render(request, 'escape/admin_terminal.html', {'output': output})


# Add-room form view
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


# Upload JSON view
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

