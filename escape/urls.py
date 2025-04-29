from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('room/', views.room_view, name='room'),
    path('success/', views.success_view, name='success'),
]
