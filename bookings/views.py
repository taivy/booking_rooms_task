from django.db import transaction
from rest_framework import permissions, viewsets
from rest_framework.serializers import ValidationError
from rooms.models import Room

from .models import Booking
from .serializers import BookingSerializer


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        room = serializer.validated_data["room"]
        date = serializer.validated_data["date"]
        start_time = serializer.validated_data["start_time"]
        end_time = serializer.validated_data["end_time"]
        with transaction.atomic():
            # Lock the Room row to serialize booking creation for this room
            Room.objects.select_for_update().get(pk=room.pk)
            # Check for overlapping booking in the same room
            overlap = Booking.objects.filter(
                room=room, date=date, start_time__lt=end_time, end_time__gt=start_time
            ).exists()
            if overlap:
                raise ValidationError("Room already booked for this time slot.")
            # Check if user already has booking for this time
            user_overlap = Booking.objects.filter(
                user=user, date=date, start_time__lt=end_time, end_time__gt=start_time
            ).exists()
            if user_overlap:
                raise ValidationError("You already have a booking at this time.")
            serializer.save(user=user)
