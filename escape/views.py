from django.shortcuts import render, redirect

# Create your views here.
from .models import Room
from django.http import HttpResponse
import random

def home(request):
    if 'current_room_id' not in request.session:
        first_room = Room.objects.first()
        if not first_room:
            return HttpResponse("No rooms available. Please contact administrator.", status=500)
        request.session['current_room_id'] = first_room.id
    return redirect('room')


from django.shortcuts import get_object_or_404

from django.shortcuts import render, redirect, get_object_or_404
from .models import Room
import random

def room_view(request):
    room_id = request.session.get('current_room_id')
    room = Room.objects.filter(id=room_id).first()

    if not room:
        request.session.flush()
        return redirect('home')

    error = None
    if request.method == 'POST':
        answer = request.POST.get('answer', '').strip().lower()
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

        # Check if answer is correct
        if answer == room.puzzle_answer.strip().lower():
            # Clear attempts on success
            attempts.pop(str(room_id), None)
            request.session['attempts'] = attempts

            next_room = Room.objects.filter(id__gt=room.id).first()
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

    total_rooms = Room.objects.count()
    solved_rooms = request.session.get('solved_room_ids', [])
    solved_count = len(solved_rooms)

    # Build a simple bar: "#" for solved, "-" for remaining
    progress_bar = "[" + "#" * solved_count + "-" * (total_rooms - solved_count) + "]"

    progress = {
        'solved': solved_count,
        'total': total_rooms,
        'bar': progress_bar
    }

    return render(request, 'escape/room.html', {
        'room': room,
        'error': error,
        'progress': progress
    })



def success_view(request):
    request.session.flush()
    return render(request, 'escape/success.html')


def get_progress(request):
    current_id = request.session.get('current_room_id')
    total = Room.objects.count()
    solved = Room.objects.filter(id__lt=current_id).count()
    bar = '█' * solved + '-' * (total - solved)
    return {'solved': solved, 'total': total, 'bar': bar}
