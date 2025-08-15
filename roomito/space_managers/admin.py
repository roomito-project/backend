from django.contrib import admin
from .models import SpaceManager, Space, Reservation, Schedule, Event, SpaceFeature
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.core.mail import send_mail

admin.site.register(Space)
admin.site.register(Reservation)
admin.site.register(Schedule)
admin.site.register(Event)
admin.site.register(SpaceFeature)

@admin.register(SpaceManager)
class SpaceManagerAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "username", "email")
    search_fields = ("first_name", "last_name", "username", "email")
    exclude = ("user",)

    def save_model(self, request, obj, form, change):
        if not change and not obj.user_id:
            temp_password = get_random_string(length=10, allowed_chars='abcdefghijklmnopqrstuvwxyz!@#$%^&*')
            user = User.objects.create_user(
                username=obj.username,
                password=temp_password,
                email=obj.email,
                first_name=obj.first_name,
                last_name=obj.last_name
            )
            obj.user = user

            send_mail(
                subject=" اطلاعات ورود مدیر فضا در رومیتو",
                message=(
                    f"مدیر محترم {obj.first_name} {obj.last_name}،\n\n"
                    f"حساب کاربری شما در سامانه مدیریت فضا ایجاد شد.\n\n"
                    f"نام کاربری: {user.username}\n"
                    f"رمز عبور موقت: {temp_password}\n\n"
                    "لطفاً پس از ورود، رمز عبور خود را تغییر دهید."
                ),
                from_email="mahyajfri37@gmail.com",
                recipient_list=[obj.email],
                fail_silently=False
            )

        super().save_model(request, obj, form, change)
