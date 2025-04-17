from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "date", "start_time", "end_time")
    search_fields = ("room__name", "user__username")
    list_filter = ("date", "room")
