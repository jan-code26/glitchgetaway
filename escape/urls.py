from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('room/', views.room_view, name='room'),
    path('success/', views.success_view, name='success'),
    path('admin-terminal/', views.admin_terminal, name='admin_terminal'),
    path('admin-add-room/', views.admin_add_room, name='admin_add_room'),
    path('admin-upload-rooms/', views.admin_upload_rooms, name='admin_upload_rooms'),
]
