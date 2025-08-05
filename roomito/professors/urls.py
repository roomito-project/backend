from django.urls import path
from .views import ProfessorRegisterView, ProfessorLoginView, ProfessorProfileUpdateView

urlpatterns = [
    path('professor/register/', ProfessorRegisterView.as_view(), name='professor-register'),
    path('professor/login/', ProfessorLoginView.as_view(), name='professor-login'),
    path('professor/updateProfile/', ProfessorProfileUpdateView.as_view(), name='professor-profile-update')
]