# Gmail & Celery Setup Guide

## Overview

1. **Gmail Configuration**:
   - SMTP server: `smtp.gmail.com`
   - Port: 587 with TLS encryption
   - Authentication requires App Password (not regular password)

2. **Celery Configuration**:
   - Broker: Redis at `localhost:6379`
   - Worker command: `python3 -m celery -A event_management worker -l info`
   - Asynchronous email sending for registration/cancellation events

## How to Get Gmail App Password

1. Go to Google Account: https://myaccount.google.com/
2. Navigate to Security → 2-Step Verification (must be enabled)
3. Go to: https://myaccount.google.com/apppasswords
4. Create new App Password for "Mail"
5. Copy the 16-character password

## Environment Configuration (.env)

```env
# Email configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx  # 16-character App Password
DEFAULT_FROM_EMAIL=your_email@gmail.com
```

## Running Celery

### Local Development:
```bash
# Terminal 1 - Celery Worker
python3 -m celery -A event_management worker -l info

# Terminal 2 - Celery Beat (for scheduled tasks)
python3 -m celery -A event_management beat -l info
```

### Docker:
```bash
docker-compose up -d celery celery-beat
```

## Testing

### 1. Direct Email Sending:
```python
from django.core.mail import send_mail
send_mail(
    'Test Subject',
    'Test message',
    'from@example.com',
    ['to@example.com'],
    fail_silently=False,
)
```

### 2. Via API (automatically through Celery):
- Event registration: `POST /api/events/{id}/register/`
- Cancel registration: `POST /api/events/{id}/unregister/`

## Email Notifications

1. **On Registration**: Confirmation with event details
2. **On Cancellation**: Cancellation confirmation
3. **Reminders**: (can be configured via Celery Beat)

## Verification

If everything is working correctly, you'll see in Celery logs:
```
[INFO/ForkPoolWorker-1] Task events.tasks.send_registration_email succeeded
[INFO/ForkPoolWorker-2] Task events.tasks.send_cancellation_email succeeded
```

## Troubleshooting

1. **"Authentication failed"**: Check App Password
2. **Emails not sending**: Check if Celery is running
3. **"Connection refused"**: Check if Redis is running (`redis-cli ping`)