from django.conf import settings
from django.db import models
from rooms.models import Room


class Booking(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings"
    )
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="bookings")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        indexes = [
            models.Index(fields=["room", "date", "start_time", "end_time"]),
            models.Index(fields=["user", "date", "start_time", "end_time"]),
        ]

    def __str__(self):
        return f"{self.room.name} booked by {self.user.username} on {self.date} from {self.start_time} to {self.end_time}"
