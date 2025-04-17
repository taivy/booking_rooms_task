from concurrent.futures import ThreadPoolExecutor
from datetime import date

import requests
from django.contrib.auth.models import User
from django.test import LiveServerTestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rooms.models import Room

from .models import Booking


class BookingAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.user1 = User.objects.create_user("user1", "user1@test.com", "pass")
        self.user2 = User.objects.create_user("user2", "user2@test.com", "pass")
        self.room = Room.objects.create(name="test room", capacity=1, floor=1)
        self.booking_url = reverse("booking-list")
        self.data = {
            "room": self.room.id,
            "date": date.today(),
            "start_time": "10:00",
            "end_time": "11:00",
        }

    def test_user_can_book_room(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.booking_url, self.data)
        self.assertEqual(response.status_code, 201)

    def test_user_cannot_book_room_without_specific_time(self):
        self.client.force_authenticate(user=self.user1)
        data = self.data.copy()
        del data["start_time"]
        del data["end_time"]
        response = self.client.post(self.booking_url, data)
        self.assertEqual(response.status_code, 400)

    def test_booking_room_same_time_not_allowed(self):
        Booking.objects.create(
            user=self.user1,
            room=self.room,
            date=date.today(),
            start_time="10:00",
            end_time="11:00",
        )
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(self.booking_url, self.data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Room already booked for this time slot", str(response.data))

    def test_booking_overlapping_time_not_allowed(self):
        Booking.objects.create(
            user=self.user1,
            room=self.room,
            date=date.today(),
            start_time="10:00",
            end_time="11:00",
        )
        self.client.force_authenticate(user=self.user1)
        data2 = self.data.copy()
        data2["start_time"] = "10:30"
        data2["end_time"] = "11:30"
        response = self.client.post(self.booking_url, data2)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Room already booked for this time slot", str(response.data))

    def test_user_sees_only_own_bookins(self):
        Booking.objects.create(
            user=self.user1,
            room=self.room,
            date=date.today(),
            start_time="10:00",
            end_time="11:00",
        )
        Booking.objects.create(
            user=self.user2,
            room=self.room,
            date=date.today(),
            start_time="11:00",
            end_time="12:00",
        )
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.booking_url)
        self.assertEqual(len(response.data), 1)

    def test_admin_sees_all_bookings(self):
        Booking.objects.create(
            user=self.user1,
            room=self.room,
            date=date.today(),
            start_time="10:00",
            end_time="11:00",
        )
        Booking.objects.create(
            user=self.user2,
            room=self.room,
            date=date.today(),
            start_time="11:00",
            end_time="12:00",
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.booking_url)
        self.assertEqual(len(response.data), 2)


class BookingAPILiveTests(LiveServerTestCase):
    def setUp(self):
        self.user1 = User.objects.create_user("user1", "user1@test.com", "pass")
        self.user2 = User.objects.create_user("user2", "user2@test.com", "pass")
        self.room = Room.objects.create(name="test room", capacity=1, floor=1)

    @staticmethod
    def get_jwt_token(user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_race_condition_simultaneous_booking(self):
        """
        Simulate two users trying to book the same room at the same time.
        Only one booking should succeed.
        """
        data = {
            "room": self.room.id,
            "date": date.today().isoformat(),
            "start_time": "14:00",
            "end_time": "15:00",
        }

        booking_url = reverse("booking-list")
        url = f"{self.live_server_url}{booking_url}"
        headers1 = {"Authorization": f"Bearer {self.get_jwt_token(self.user1)}"}
        headers2 = {"Authorization": f"Bearer {self.get_jwt_token(self.user2)}"}

        def book_with_headers(headers):
            return requests.post(url, json=data, headers=headers)

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(book_with_headers, headers1),
                executor.submit(book_with_headers, headers2),
            ]
            results = [f.result() for f in futures]
        # One booking should succeed, the other should fail
        has_succeded_booking = any(r.status_code == 201 for r in results)
        has_failed_booking = any(r.status_code == 400 for r in results)
        self.assertTrue(has_succeded_booking)
        self.assertTrue(has_failed_booking)
