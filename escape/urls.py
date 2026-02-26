from django.urls import path
from . import views

urlpatterns = [
    path('', views.portfolio, name='portfolio'),  # Portfolio homepage
    path('play/', views.home, name='home'),  # Game entry point - redirects to play/room/
    path('play/room/', views.room_view, name='room'),  # Active game room
    path('play/success/', views.success_view, name='success'),  # Game completion
    path('play/admin-terminal/', views.admin_terminal, name='admin_terminal'),
    path('play/admin-add-room/', views.admin_add_room, name='admin_add_room'),
    path('play/admin-upload-rooms/', views.admin_upload_rooms, name='admin_upload_rooms'),
    path('healthz/', views.health_check, name='health_check'),  # Health check endpoint
]
