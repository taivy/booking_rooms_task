from django.contrib import admin

from .models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity", "floor")
    search_fields = ("name",)
    list_filter = ("floor", "capacity")
