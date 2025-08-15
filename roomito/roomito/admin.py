from django.contrib import admin
from django.contrib.auth.models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'first_name', 'last_name', 'is_staff') 
    list_display_links = ('id', 'email', 'first_name')