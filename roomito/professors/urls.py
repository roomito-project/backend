from django.urls import path
from .views import ProfessorRegisterView, ProfessorVerifyView

urlpatterns = [
    path('professor/register/', ProfessorRegisterView.as_view(), name='professor-register'),
    path('professor/verify/', ProfessorVerifyView.as_view(), name='professor-verify'),
]