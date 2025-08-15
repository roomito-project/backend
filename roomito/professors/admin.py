from django.contrib import admin
from .models import Professor

@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('id','first_name', 'last_name', 'email', 'personnel_code', 'national_id', 'is_registered')
    fields = (
        'first_name', 'last_name', 'email',
    )
    search_fields = ('first_name', 'last_name', 'email', 'personnel_code')
