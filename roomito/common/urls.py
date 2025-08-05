from django.urls import path
from .views import UnifiedLoginView

urlpatterns = [
    path('login/', UnifiedLoginView.as_view(), name='unified-login'),
]