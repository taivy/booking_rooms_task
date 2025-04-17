from datetime import datetime

from bookings.models import Booking
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Room
from .serializers import RoomSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]
    filterset_fields = ["capacity", "floor"]

    @action(detail=False, methods=["get"], url_path="available")
    def available(self, request):
        date_str = request.query_params.get("date")
        date = None
        if date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"detail": "Invalid date format. Use YYYY-MM-DD."}, status=400
                )
        start_time_str = request.query_params.get("start_time")
        end_time_str = request.query_params.get("end_time")
        capacity = request.query_params.get("capacity")
        floor = request.query_params.get("floor")

        start_time = None
        end_time = None
        if start_time_str:
            try:
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
            except ValueError:
                return Response(
                    {"detail": "Invalid start_time format. Use HH:MM."}, status=400
                )
        if end_time_str:
            try:
                end_time = datetime.strptime(end_time_str, "%H:%M").time()
            except ValueError:
                return Response(
                    {"detail": "Invalid end_time format. Use HH:MM."}, status=400
                )

        rooms = Room.objects.all()
        if capacity:
            rooms = rooms.filter(capacity=capacity)
        if floor:
            rooms = rooms.filter(floor=floor)

        if date and start_time and end_time:
            overlapping_bookings = Booking.objects.filter(
                date=date, start_time__lt=end_time, end_time__gt=start_time
            )
            booked_room_ids = list(
                overlapping_bookings.values_list("room_id", flat=True)
            )
            rooms = rooms.exclude(id__in=booked_room_ids)

        rooms = rooms.prefetch_related("bookings")
        serializer = self.get_serializer(rooms, many=True)
        return Response(serializer.data)
