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
        if answer == room.puzzle_answer.strip().lower():
            # Mark as solved
            solved_rooms = request.session.get('solved_room_ids', [])
            if room.id not in solved_rooms:
                solved_rooms.append(room.id)
                request.session['solved_room_ids'] = solved_rooms

            # Pick random unsolved room
            unsolved_rooms = Room.objects.exclude(id__in=solved_rooms)
            if unsolved_rooms.exists():
                next_room = random.choice(list(unsolved_rooms))
                request.session['current_room_id'] = next_room.id
                return redirect('room')
            else:
                return redirect('success')
        else:
            error = ">> Incorrect answer. Try again."
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
