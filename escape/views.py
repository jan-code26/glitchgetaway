from django.shortcuts import render, redirect

# Create your views here.
from .models import Room
from django.http import HttpResponse

def home(request):
    if 'current_room_id' not in request.session:
        first_room = Room.objects.first()
        if not first_room:
            return HttpResponse("No rooms available. Please contact administrator.", status=500)
        request.session['current_room_id'] = first_room.id
    return redirect('room')


from django.shortcuts import get_object_or_404

def room_view(request):
    room_id = request.session.get('current_room_id')

    # Safely fetch the room
    room = Room.objects.filter(id=room_id).first()

    if not room:
        # Room not found -> reset session and redirect to home
        request.session.flush()
        return redirect('home')

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
