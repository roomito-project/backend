from django.urls import path
from . import views
from .views import StudentRegisterView, StudentProfileUpdateView

urlpatterns = [
    path('student/Register/', StudentRegisterView.as_view(), name='student-register'),
    path('student/updateProfile/', StudentProfileUpdateView.as_view(), name='student-update-profile')
]