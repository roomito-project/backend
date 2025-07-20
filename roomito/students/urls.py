from django.urls import path
from . import views
from .views import StudentRegisterView, StudentLoginView

urlpatterns = [
    path('student/Register/', StudentRegisterView.as_view(), name='register'),
    path('student/login/', StudentLoginView.as_view(), name='login'),    
]