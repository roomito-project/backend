from django.urls import path
from .views import ProfessorRegisterView, ProfessorVerifyView, ProfessorLoginView, ProfessorResendVerificationView

urlpatterns = [
    path('professor/register/', ProfessorRegisterView.as_view(), name='professor-register'),
    path('professor/verify/', ProfessorVerifyView.as_view(), name='professor-verify'),
    path('professor/login/', ProfessorLoginView.as_view(), name='professor-login'),
    path('professor/resendVerificationCode/', ProfessorResendVerificationView.as_view(), name='professor-resend-verification-code')
]