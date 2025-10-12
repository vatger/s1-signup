from django.urls import path
from .views import get_roster

urlpatterns = [
    path('', get_roster, name='get-roster'),
]