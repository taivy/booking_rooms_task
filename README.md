# Meeting Room Booking API

REST API for booking meeting rooms in an office, built on Django 4.2, DRF, PostgreSQL, and Docker. Supports JWT authentication, admin/user roles, room management, booking logic, and API documentation.

## Deploying the project

Build and start:

```sh
docker-compose up --build -d
```

The app is available on http://localhost:8000/.

To run tests:

```sh
docker-compose exec web python manage.py test
```

Create super user:

```sh
docker-compose exec web python manage.py createsuperuser
```

## URLs
- API root endpoint: http://localhost:8000/api/
- Django admin panel: http://localhost:8000/admin/
- Swagger docs: http://localhost:8000/swagger/

## API Overview

### Authentication
- `POST /api/auth/register/`: Register new user
- `POST /api/auth/login/`: Obtain JWT token
- `POST /api/auth/token/refresh/`: Refresh JWT token
- `GET /api/auth/user/`: Get current user details

### Rooms
- `GET /api/rooms/`: List rooms
- `GET /api/rooms/available/?date=YYYY-MM-DD&start_time=HH:MM&end_time=HH:MM&capacity=&floor=`: List available rooms (filter by capacity, floor, date, time)
- `POST /api/rooms/`: Create room (admin only)
- `PUT/PATCH/DELETE /api/rooms/{id}/`: Update/delete room (admin only)

### Bookings
- `GET /api/bookings/`: List bookings (user: own bookings, admin: all bookings)
- `POST /api/bookings/`: Book a room
- `PUT/PATCH/DELETE /api/bookings/{id}/`: Manage booking (owner or admin)

## (Potentially) TODO / "capacity" notes

If capacity is meant to be not just a field/property of rooms, like floor, but rather a limit on the number of people that can use a room, then logic and tests need to be updated (e.g. if room's capacity is 3 and someone booked it for 10:00-11:00, then it's still available to be booked for 10:00-11:00 for 2 more users).
