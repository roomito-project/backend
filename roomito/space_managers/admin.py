from django.contrib import admin
from .models import SpaceManager, Space, Reservation, Schedule, Event

admin.site.register(SpaceManager)
admin.site.register(Space)
admin.site.register(Reservation)
admin.site.register(Schedule)
admin.site.register(Event)