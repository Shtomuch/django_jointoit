# Event Management REST API

A production-ready Django REST API for managing events and registrations. Built with Django REST Framework, JWT authentication, Celery for async tasks, and PostgreSQL database with query optimizations.

## Features

- **User Authentication**: JWT-based authentication system
- **Event Management**: Full CRUD operations for events
- **Event Registration**: Users can register/unregister for events
- **Advanced Search & Filtering**: Search events by title, location, date range, availability
- **Email Notifications**: Automated emails for registrations and cancellations via Celery
- **API Documentation**: Interactive API docs with Swagger/ReDoc
- **Docker Support**: Full Docker containerization with docker-compose
- **Database Optimization**: Efficient queries with select_related, prefetch_related, and indexes

## Tech Stack

- Django 5.2.4
- Django REST Framework 3.16.0
- PostgreSQL 16
- Redis 7
- Celery 5.5.3
- Docker & Docker Compose
- JWT Authentication

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Installation with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd django_jointoit
```

2. Create `.env` file with your configuration:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Build and run with Docker Compose:
```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

### Local Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run PostgreSQL and Redis locally or update `.env` with your database credentials

4. Run migrations:
```bash
python manage.py migrate
```

5. Create superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## API Endpoints

### Authentication Endpoints

#### User Registration
- **Endpoint**: `POST /api/auth/register/`
- **Purpose**: Create a new user account in the system
- **Authentication**: Not required
- **Request Body**:
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "SecurePass123!",
  "password2": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```
- **Success Response** (201 Created):
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```
- **Error Response** (400 Bad Request):
```json
{
  "username": ["A user with that username already exists."],
  "password": ["Password fields didn't match."]
}
```

#### User Login
- **Endpoint**: `POST /api/auth/login/`
- **Purpose**: Authenticate user and receive JWT access and refresh tokens
- **Authentication**: Not required
- **Request Body**:
```json
{
  "username": "testuser",
  "password": "testpass123"
}
```
- **Success Response** (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User"
  }
}
```
- **Error Response** (401 Unauthorized):
```json
{
  "detail": "No active account found with the given credentials"
}
```

#### Token Refresh
- **Endpoint**: `POST /api/auth/token/refresh/`
- **Purpose**: Get a new access token using the refresh token
- **Authentication**: Not required
- **Request Body**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```
- **Success Response** (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Get User Profile
- **Endpoint**: `GET /api/auth/profile/`
- **Purpose**: Retrieve the current authenticated user's profile information
- **Authentication**: Required (Bearer token)
- **Success Response** (200 OK):
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "first_name": "Test",
  "last_name": "User"
}
```

#### Update User Profile
- **Endpoint**: `PUT /api/auth/profile/update/`
- **Purpose**: Update the authenticated user's profile information
- **Authentication**: Required (Bearer token)
- **Request Body**:
```json
{
  "username": "updateduser",
  "email": "updated@example.com",
  "first_name": "Updated",
  "last_name": "Name"
}
```
- **Success Response** (200 OK):
```json
{
  "username": "updateduser",
  "email": "updated@example.com",
  "first_name": "Updated",
  "last_name": "Name"
}
```

#### Change Password
- **Endpoint**: `POST /api/auth/change-password/`
- **Purpose**: Change the authenticated user's password
- **Authentication**: Required (Bearer token)
- **Request Body**:
```json
{
  "old_password": "currentPassword123",
  "new_password": "newSecurePassword123!"
}
```
- **Success Response** (200 OK):
```json
{
  "detail": "Password updated successfully"
}
```
- **Error Response** (400 Bad Request):
```json
{
  "old_password": ["Old password is not correct"]
}
```

### Event Management Endpoints

#### List Events
- **Endpoint**: `GET /api/events/`
- **Purpose**: Get a paginated list of all events with optional filtering and search
- **Authentication**: Not required
- **Query Parameters**:
  - `page`: Page number for pagination
  - `search`: Search in title, description, and location
  - `organizer`: Filter by organizer ID
  - `date_after`: Filter events after this date (YYYY-MM-DD)
  - `date_before`: Filter events before this date (YYYY-MM-DD)
  - `is_active`: Filter by active status (true/false)
  - `has_spots`: Filter events with available spots (true/false)
  - `ordering`: Order by field (date, -date, created_at, -created_at, title, -title)
- **Success Response** (200 OK):
```json
{
  "count": 100,
  "next": "http://api.example.com/events/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Django Conference 2024",
      "description": "Annual Django developers conference",
      "date": "2024-06-15T09:00:00Z",
      "location": "San Francisco, CA",
      "organizer_name": "John Doe",
      "attendees_count": 45,
      "available_spots": 55,
      "is_active": true,
      "is_past": false
    }
  ]
}
```

#### Create Event
- **Endpoint**: `POST /api/events/`
- **Purpose**: Create a new event. The authenticated user becomes the organizer.
- **Authentication**: Required (Bearer token)
- **Request Body**:
```json
{
  "title": "Python Workshop",
  "description": "Hands-on Python programming workshop for beginners",
  "date": "2024-07-20T14:00:00Z",
  "location": "Tech Hub, New York",
  "max_attendees": 30
}
```
- **Success Response** (201 Created):
```json
{
  "id": 2,
  "title": "Python Workshop",
  "description": "Hands-on Python programming workshop for beginners",
  "date": "2024-07-20T14:00:00Z",
  "location": "Tech Hub, New York",
  "organizer": 1,
  "organizer_name": "Jane Smith",
  "max_attendees": 30,
  "attendees_count": 0,
  "available_spots": 30,
  "is_active": true,
  "is_past": false,
  "created_at": "2024-01-10T10:00:00Z",
  "updated_at": "2024-01-10T10:00:00Z"
}
```

#### Get Event Details
- **Endpoint**: `GET /api/events/{id}/`
- **Purpose**: Retrieve detailed information about a specific event
- **Authentication**: Not required
- **Success Response** (200 OK):
```json
{
  "id": 1,
  "title": "Django Conference 2024",
  "description": "Annual Django developers conference",
  "date": "2024-06-15T09:00:00Z",
  "location": "San Francisco, CA",
  "organizer": 1,
  "organizer_name": "John Doe",
  "max_attendees": 100,
  "attendees_count": 45,
  "available_spots": 55,
  "is_active": true,
  "is_past": false,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-05T15:30:00Z"
}
```

#### Update Event
- **Endpoint**: `PUT /api/events/{id}/`
- **Purpose**: Update all fields of an event (full update)
- **Authentication**: Required (Bearer token, must be event organizer)
- **Request Body**: Same as create event
- **Success Response** (200 OK): Returns updated event data

#### Partial Update Event
- **Endpoint**: `PATCH /api/events/{id}/`
- **Purpose**: Update specific fields of an event
- **Authentication**: Required (Bearer token, must be event organizer)
- **Request Body Example**:
```json
{
  "max_attendees": 200,
  "location": "Updated location"
}
```

#### Delete Event
- **Endpoint**: `DELETE /api/events/{id}/`
- **Purpose**: Delete an event permanently
- **Authentication**: Required (Bearer token, must be event organizer)
- **Success Response** (204 No Content): Empty response

#### Get Upcoming Events
- **Endpoint**: `GET /api/events/upcoming/`
- **Purpose**: Get all active events scheduled for the future
- **Authentication**: Not required
- **Success Response** (200 OK): Same format as list events

#### Get My Organized Events
- **Endpoint**: `GET /api/events/my_events/`
- **Purpose**: Get all events organized by the authenticated user
- **Authentication**: Required (Bearer token)
- **Success Response** (200 OK): Same format as list events

### Event Registration Endpoints

#### Register for Event
- **Endpoint**: `POST /api/events/{id}/register/`
- **Purpose**: Register the authenticated user for an event
- **Authentication**: Required (Bearer token)
- **Success Response** (201 Created):
```json
{
  "id": 10,
  "user": 2,
  "event": 1,
  "registered_at": "2024-01-10T15:30:00Z",
  "is_cancelled": false
}
```
- **Error Responses**:
  - 400: "You are already registered for this event."
  - 400: "This event is full."
  - 400: "Cannot register for past events."
  - 400: "This event is not active."

#### Unregister from Event
- **Endpoint**: `POST /api/events/{id}/unregister/`
- **Purpose**: Cancel registration for an event
- **Authentication**: Required (Bearer token)
- **Success Response** (200 OK):
```json
{
  "detail": "Successfully unregistered from the event."
}
```
- **Error Response** (400 Bad Request):
```json
{
  "detail": "You are not registered for this event."
}
```

#### Get Event Attendees
- **Endpoint**: `GET /api/events/{id}/attendees/`
- **Purpose**: Get list of registered attendees for an event
- **Authentication**: Required (Bearer token, must be event organizer)
- **Success Response** (200 OK):
```json
{
  "count": 15,
  "results": [
    {
      "id": 5,
      "user": 3,
      "event": 1,
      "registered_at": "2024-01-05T10:00:00Z",
      "is_cancelled": false
    }
  ]
}
```
- **Error Response** (403 Forbidden):
```json
{
  "detail": "Only the organizer can view attendees."
}
```

### Registration Management Endpoints

#### My Registrations
- **Endpoint**: `GET /api/my-registrations/`
- **Purpose**: Get all event registrations for the authenticated user
- **Authentication**: Required (Bearer token)
- **Success Response** (200 OK):
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "event": {
        "id": 1,
        "title": "Django Conference",
        "date": "2024-06-15T09:00:00Z"
      },
      "registered_at": "2024-01-01T10:00:00Z",
      "is_cancelled": false
    }
  ]
}
```

#### Active Registrations
- **Endpoint**: `GET /api/my-registrations/active/`
- **Purpose**: Get all active (not cancelled) registrations for upcoming events
- **Authentication**: Required (Bearer token)
- **Success Response** (200 OK): Same format as my registrations

#### Past Registrations
- **Endpoint**: `GET /api/my-registrations/past/`
- **Purpose**: Get all registrations for past events
- **Authentication**: Required (Bearer token)
- **Success Response** (200 OK): Same format as my registrations

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

## Search and Filtering

Events can be filtered and searched using query parameters. Multiple filters can be combined:

### Example Queries

1. **Search for Python events in New York with available spots**:
```
GET /api/events/?search=python&location=New York&has_spots=true
```

2. **Get events between specific dates**:
```
GET /api/events/?date_after=2024-01-01&date_before=2024-12-31
```

3. **Get events by a specific organizer, ordered by date**:
```
GET /api/events/?organizer=1&ordering=-date
```

### Available Filters

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search in title, description, and location fields |
| `title` | string | Filter by exact title (case-insensitive) |
| `location` | string | Filter by location (case-insensitive, partial match) |
| `date_after` | date | Events on or after this date (YYYY-MM-DD) |
| `date_before` | date | Events on or before this date (YYYY-MM-DD) |
| `organizer` | integer | Filter by organizer user ID |
| `has_spots` | boolean | true = events with available spots, false = full events |
| `is_past` | boolean | true = past events, false = future events |
| `is_active` | boolean | true = active events, false = inactive events |
| `ordering` | string | Sort by: date, -date, created_at, -created_at, title, -title |
| `page` | integer | Page number for pagination |
| `page_size` | integer | Number of results per page (default: 20) |

## Email Configuration

Configure email settings in `.env`:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

## Running Celery Workers

For email notifications to work, run Celery workers:

```bash
# With Docker
docker-compose up celery celery-beat

# Locally
celery -A event_management worker -l info
celery -A event_management beat -l info
```

## Database Optimizations

The API implements several database optimizations:

1. **Indexed fields**: `title`, `date`, combined indexes for common queries
2. **Select/Prefetch Related**: Optimized queries to prevent N+1 problems
3. **Annotated queries**: Attendee counts calculated at database level
4. **Efficient filtering**: Database-level filtering for event availability

## Testing

Run tests with:
```bash
python manage.py test
```

## Authentication

### JWT Token Usage

The API uses JWT (JSON Web Tokens) for authentication. After login, you'll receive:
- **Access Token**: Valid for 60 minutes, used for API requests
- **Refresh Token**: Valid for 7 days, used to get new access tokens

### Making Authenticated Requests

Include the access token in the Authorization header:
```bash
curl -H "Authorization: Bearer <your-access-token>" http://localhost:8000/api/events/my_events/
```

### Token Refresh

When the access token expires, use the refresh token to get a new one:
```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<your-refresh-token>"}'
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key (keep secure in production) | `django-insecure-...` |
| `DB_HOST` | PostgreSQL host | `localhost` or `db` (Docker) |
| `DB_USER` | PostgreSQL username | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | `yourpassword` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
| `EMAIL_HOST` | SMTP server host | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP server port | `587` |
| `EMAIL_USE_TLS` | Use TLS for email | `True` |
| `EMAIL_HOST_USER` | Email username | `''` |
| `EMAIL_HOST_PASSWORD` | Email password | `''` |
| `DEFAULT_FROM_EMAIL` | Default sender email | `noreply@eventmanagement.com` |


### Docker Production Setup

```bash
# Build production image
docker build -t event-management:latest .

# Run with production settings
docker run -d \
  --name event-api \
  -p 8000:8000 \
  --env-file .env.production \
  event-management:latest
```
