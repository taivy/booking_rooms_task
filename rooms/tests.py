from datetime import date, time

from bookings.models import Booking
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Room


class RoomAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.user = User.objects.create_user("user", "user@test.com", "pass")
        self.room1 = Room.objects.create(name="Room A", capacity=1, floor=1)
        self.room2 = Room.objects.create(name="Room B", capacity=1, floor=1)
        self.room3 = Room.objects.create(name="Room C", capacity=1, floor=2)

    def test_rooms_list_access(self):
        response = self.client.get(reverse("room-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    def test_room_detail_access(self):
        """
        Ensure both regular users and admins can access the room detail endpoint.
        """
        url = reverse("room-detail", args=[self.room1.id])
        expected_response = {
            "name": "Room A",
            "capacity": 1,
            "floor": 1,
            "id": self.room1.id,
        }
        # Access the endpoint as regular user
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_response)
        # Access the endpoint as admin
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_response)

    def test_create_room_admin_only(self):
        payload = {"name": "Room D", "capacity": 1, "floor": 2}
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("room-list"), payload)
        self.assertEqual(response.status_code, 403)
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(reverse("room-list"), payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Room.objects.count(), 4)

    def test_edit_room_admin_only(self):
        url = reverse("room-detail", args=[self.room1.id])
        update_data = {"name": "Room A Updated", "capacity": 2, "floor": 1}
        # Regular user cannot update
        self.client.force_authenticate(user=self.user)
        response = self.client.put(url, update_data)
        self.assertEqual(response.status_code, 403)
        response = self.client.patch(url, {"name": "Room A Updated"})
        self.assertEqual(response.status_code, 403)
        # Admin can update
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(url, update_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Room A Updated")

    def test_delete_room_admin_only(self):
        url = reverse("room-detail", args=[self.room1.id])
        # Regular user cannot delete
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)
        # Admin can delete
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Room.objects.filter(id=self.room1.id).exists())

    def test_available_rooms(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("room-available")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # All 3 rooms are available
        self.assertEqual(len(response.data), 3)

    def test_available_rooms_filtering_date(self):
        """
        Test filtering available rooms by date, capacity, and floor.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse("room-available")
        booking_date = date.today()
        booking_date_str = booking_date.isoformat()
        params = {
            "date": booking_date_str,
            "capacity": 1,
            "floor": 1,
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        rooms_names = {d["name"] for d in response.data}
        # Room C isn't there because floor parameter doesn't match
        self.assertEqual(rooms_names, {"Room A", "Room B"})
        # Book room A for a time slot
        Booking.objects.create(
            user=self.user,
            room=self.room1,
            date=booking_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
        )
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        # Both rooms A and B are available because we filter by date without specific time
        self.assertEqual(len(response.data), 2)
        rooms_names = {d["name"] for d in response.data}
        self.assertEqual(rooms_names, {"Room A", "Room B"})

    def test_available_rooms_filtering_time(self):
        """
        Test filtering available rooms by date, capacity, and floor.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse("room-available")
        booking_date = date.today()
        booking_date_str = booking_date.isoformat()
        params = {
            "date": booking_date_str,
            "floor": 1,
            "start_time": "10:01",
            "end_time": "10:30",
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        rooms_names = {d["name"] for d in response.data}
        # Room C isn't there because floor parameter doesn't match
        self.assertEqual(rooms_names, {"Room A", "Room B"})
        # Book room A for a time slot
        Booking.objects.create(
            user=self.user,
            room=self.room1,
            date=booking_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
        )
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        # Only room B should be available because room A is booked
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Room B")
        # Check another overlap
        params = params.copy()
        params["start_time"] = "10:30"
        params["end_time"] = "11:30"
        response = self.client.get(url, params)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Room B")
        # Check another overlap
        params = params.copy()
        params["start_time"] = "09:45"
        params["end_time"] = "11:15"
        response = self.client.get(url, params)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Room B")
        # Check exact overlap
        params = params.copy()
        params["start_time"] = "10:00"
        params["end_time"] = "11:00"
        response = self.client.get(url, params)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Room B")
