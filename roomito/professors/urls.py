from django.urls import path
from .views import ProfessorRegisterView, ProfessorProfileUpdateView, ProfessorProfileView

urlpatterns = [
    path('professor/register/', ProfessorRegisterView.as_view(), name='professor-register'),
    path('professor/updateProfile/', ProfessorProfileUpdateView.as_view(), name='professor-profile-update'),
    path('professor/profile/', ProfessorProfileView.as_view(), name='professor-profile')
]