from django.shortcuts import render, redirect

# Create your views here.
from .models import Room

def home(request):
    if 'current_room_id' not in request.session:
        first_room = Room.objects.first()
        request.session['current_room_id'] = first_room.id
    return redirect('room')

def room_view(request):
    room_id = request.session.get('current_room_id')
    room = Room.objects.get(id=room_id)

    if request.method == 'POST':
        answer = request.POST.get('answer', '').strip().lower()
        if answer == room.puzzle_answer.strip().lower():
            next_room = Room.objects.filter(id__gt=room.id).first()
            if next_room:
                request.session['current_room_id'] = next_room.id
                return redirect('room')
            else:
                return redirect('success')

    return render(request, 'escape/room.html', {'room': room})

def success_view(request):
    request.session.flush()
    return render(request, 'escape/success.html')
