from django.urls import path
from . import views
from .views import StudentRegisterView, StudentLoginView, StudentProfileUpdateView

urlpatterns = [
    path('student/Register/', StudentRegisterView.as_view(), name='student-register'),
    path('student/login/', StudentLoginView.as_view(), name='student-login'),    
    path('student/updateProfile/', StudentProfileUpdateView.as_view(), name='student-update-profile')
]