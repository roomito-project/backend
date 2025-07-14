from django.contrib import admin
from .models import SpaceManager
from .models import Reservation

admin.site.register(SpaceManager)
admin.site.register(Reservation)