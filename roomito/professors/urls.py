from django.urls import path
from .views import ProfessorRegisterView, ProfessorVerifyView, ProfessorLoginView

urlpatterns = [
    path('professor/register/', ProfessorRegisterView.as_view(), name='professor-register'),
    path('professor/verify/', ProfessorVerifyView.as_view(), name='professor-verify'),
    path('professor/login/', ProfessorLoginView.as_view(), name='professor-login'),
]