from django.urls import path
from .views import StaffRegisterView, StaffProfileUpdateView, StaffProfileView

urlpatterns = [
    path('staff/register/', StaffRegisterView.as_view(), name='staff-register'),
    path('staff/updateProfile/', StaffProfileUpdateView.as_view(), name='staff-profile-update'),
    path('staff/profile/', StaffProfileView.as_view(), name='staff-profile')
]