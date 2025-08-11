# students/admin.py
from django.contrib import admin, messages
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'get_first_name', 'get_last_name','student_id', 'national_id', 'is_approved', 'student_card_photo',
    )
    list_filter = ('is_approved',)
    search_fields = (
        'user__first_name', 'user__last_name', 'user__email',
    )
    actions = ['approve_students', 'revoke_approval']

    @admin.display(description='First name')
    def get_first_name(self, obj):
        return obj.user.first_name

    @admin.display(description='Last name')
    def get_last_name(self, obj):
        return obj.user.last_name

    @admin.action(description="Confirm selected students and send notification email")
    def approve_students(self, request, queryset):
        approved_cnt = 0
        emailed_cnt = 0
        failed_emails = []

        with transaction.atomic():
            for student in queryset.select_related('user'):
                if student.is_approved:
                    continue

                student.is_approved = True
                student.save(update_fields=['is_approved'])
                approved_cnt += 1

                try:
                    send_mail(
                        subject="تأیید ثبت‌نام دانشجو در رومیتو",
                        message=(
                            f"دانشجوی گرامی {student.user.first_name} {student.user.last_name}،\n"
                            "ثبت‌نام شما توسط مدیر سامانه تأیید شد. اکنون می‌توانید وارد حساب کاربری خود شوید."
                        ),
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or settings.EMAIL_HOST_USER,
                        recipient_list=[student.user.email],
                        fail_silently=False,
                    )
                    emailed_cnt += 1
                except Exception as e:
                    failed_emails.append((student.student_id, str(e)))

        if approved_cnt:
            self.message_user(
                request,
                f"{approved_cnt} student(s) approved. Emails sent successfully: {emailed_cnt}.",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "No students were approved.",
                level=messages.INFO
            )

        if failed_emails:
            detail = "; ".join([f"{sid}: {err}" for sid, err in failed_emails[:5]])
            more = f" (+{len(failed_emails)-5} more)" if len(failed_emails) > 5 else ""
            self.message_user(
                request,
                f"Email sending failed for some students: {detail}{more}",
                level=messages.WARNING,
            )

    @admin.action(description="Revoke approval (set selected students as not approved)")
    def revoke_approval(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(
            request,
            f"{updated} student(s) approval revoked.",
            level=messages.INFO
        )

