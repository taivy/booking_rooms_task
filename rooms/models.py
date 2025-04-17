from django.db import models


class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    capacity = models.PositiveIntegerField()
    floor = models.IntegerField()

    def __str__(self):
        return f"{self.name} (Floor {self.floor}, Capacity {self.capacity})"
