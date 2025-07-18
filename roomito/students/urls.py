from django.urls import path
from . import views
from .views import RegisterView

urlpatterns = [
    path('student/Register/', RegisterView.as_view(), name='register'),
]