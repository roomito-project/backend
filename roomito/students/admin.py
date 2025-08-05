from django.contrib import admin
from .models import Student
from django.core.mail import send_mail
from django.conf import settings

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_first_name', 'get_last_name', 'is_approved', 'student_card_photo')
    actions = ['approve_students']
    search_fields = ('first_name', 'last_name', 'personnel_code', 'is_approved')

    @admin.display(description='first name')
    def get_first_name(self, obj):
        return obj.user.first_name

    @admin.display(description='last name')
    def get_last_name(self, obj):
        return obj.user.last_name

    @admin.action(description="Confirm selected students and send notification email")
    def approve_students(self, request, queryset):
        approved_count = 0
        for student in queryset:
            if not student.is_approved:
                student.is_approved = True
                student.save()
                student.send_approval_email()
                approved_count += 1

        self.message_user(request, f"{approved_count} The student has been successfully verified and the email has been sent.")
