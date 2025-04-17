from rest_framework import serializers

from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    room_name = serializers.ReadOnlyField(source="room.name")

    class Meta:
        model = Booking
        fields = ["id", "room", "room_name", "date", "start_time", "end_time"]
