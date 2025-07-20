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

### Authentication

- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - Login (returns JWT tokens)
- `POST /api/auth/token/refresh/` - Refresh JWT token
- `GET /api/auth/profile/` - Get current user profile
- `PUT /api/auth/profile/update/` - Update profile
- `POST /api/auth/change-password/` - Change password

### Events

- `GET /api/events/` - List all events (with pagination, filtering, search)
- `POST /api/events/` - Create new event (authenticated)
- `GET /api/events/{id}/` - Get event details
- `PUT /api/events/{id}/` - Update event (organizer only)
- `DELETE /api/events/{id}/` - Delete event (organizer only)
- `GET /api/events/upcoming/` - List upcoming events
- `GET /api/events/my_events/` - List user's organized events
- `POST /api/events/{id}/register/` - Register for event
- `POST /api/events/{id}/unregister/` - Unregister from event
- `GET /api/events/{id}/attendees/` - Get event attendees (organizer only)

### Registrations

- `GET /api/my-registrations/` - List user's registrations
- `GET /api/my-registrations/active/` - Active registrations
- `GET /api/my-registrations/past/` - Past registrations

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

## Search and Filtering

Events can be filtered and searched using query parameters:

```
GET /api/events/?search=python&location=New York&date_from=2024-01-01&has_spots=true
```

Available filters:
- `search` - Search in title, description, location
- `title` - Filter by title (case-insensitive)
- `location` - Filter by location (case-insensitive)
- `date_from` - Events from this date
- `date_to` - Events until this date
- `organizer` - Filter by organizer ID
- `has_spots` - Events with available spots
- `is_past` - Past events filter
- `is_active` - Active/inactive events

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

## Environment Variables

Key environment variables:

- `DEBUG` - Debug mode (default: False)
- `SECRET_KEY` - Django secret key
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `EMAIL_*` - Email configuration settings
