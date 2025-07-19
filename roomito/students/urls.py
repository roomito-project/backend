from django.urls import path
from . import views
from .views import StudentRegisterView

urlpatterns = [
    path('student/Register/', StudentRegisterView.as_view(), name='register'),
]