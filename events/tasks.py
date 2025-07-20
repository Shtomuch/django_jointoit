from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import EventRegistration


@shared_task
def send_registration_email(registration_id):
    try:
        registration = EventRegistration.objects.select_related(
            'user', 'event', 'event__organizer'
        ).get(id=registration_id)
        
        subject = f'Registration Confirmation: {registration.event.title}'
        
        context = {
            'user': registration.user,
            'event': registration.event,
            'registration': registration,
        }
        
        html_message = f"""
        <h2>Registration Confirmation</h2>
        <p>Dear {registration.user.first_name or registration.user.username},</p>
        <p>You have successfully registered for the following event:</p>
        <ul>
            <li><strong>Event:</strong> {registration.event.title}</li>
            <li><strong>Date:</strong> {registration.event.date.strftime('%B %d, %Y at %I:%M %p')}</li>
            <li><strong>Location:</strong> {registration.event.location}</li>
            <li><strong>Organizer:</strong> {registration.event.organizer.username}</li>
        </ul>
        <p>We look forward to seeing you at the event!</p>
        <p>Best regards,<br>Event Management Team</p>
        """
        
        plain_message = f"""
        Registration Confirmation
        
        Dear {registration.user.first_name or registration.user.username},
        
        You have successfully registered for the following event:
        
        Event: {registration.event.title}
        Date: {registration.event.date.strftime('%B %d, %Y at %I:%M %p')}
        Location: {registration.event.location}
        Organizer: {registration.event.organizer.username}
        
        We look forward to seeing you at the event!
        
        Best regards,
        Event Management Team
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[registration.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return f"Registration email sent to {registration.user.email}"
    
    except EventRegistration.DoesNotExist:
        return f"Registration with id {registration_id} not found"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def send_cancellation_email(registration_id):
    try:
        registration = EventRegistration.objects.select_related(
            'user', 'event', 'event__organizer'
        ).get(id=registration_id)
        
        subject = f'Registration Cancelled: {registration.event.title}'
        
        html_message = f"""
        <h2>Registration Cancellation</h2>
        <p>Dear {registration.user.first_name or registration.user.username},</p>
        <p>Your registration for the following event has been cancelled:</p>
        <ul>
            <li><strong>Event:</strong> {registration.event.title}</li>
            <li><strong>Date:</strong> {registration.event.date.strftime('%B %d, %Y at %I:%M %p')}</li>
            <li><strong>Location:</strong> {registration.event.location}</li>
        </ul>
        <p>If you wish to register again, please visit the event page.</p>
        <p>Best regards,<br>Event Management Team</p>
        """
        
        plain_message = f"""
        Registration Cancellation
        
        Dear {registration.user.first_name or registration.user.username},
        
        Your registration for the following event has been cancelled:
        
        Event: {registration.event.title}
        Date: {registration.event.date.strftime('%B %d, %Y at %I:%M %p')}
        Location: {registration.event.location}
        
        If you wish to register again, please visit the event page.
        
        Best regards,
        Event Management Team
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[registration.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return f"Cancellation email sent to {registration.user.email}"
    
    except EventRegistration.DoesNotExist:
        return f"Registration with id {registration_id} not found"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def send_event_reminder(event_id):
    """Send reminder emails to all registered users 24 hours before the event"""
    from .models import Event
    
    try:
        event = Event.objects.get(id=event_id)
        registrations = event.registrations.filter(
            is_cancelled=False
        ).select_related('user')
        
        for registration in registrations:
            subject = f'Event Reminder: {event.title}'
            
            html_message = f"""
            <h2>Event Reminder</h2>
            <p>Dear {registration.user.first_name or registration.user.username},</p>
            <p>This is a reminder that you are registered for the following event tomorrow:</p>
            <ul>
                <li><strong>Event:</strong> {event.title}</li>
                <li><strong>Date:</strong> {event.date.strftime('%B %d, %Y at %I:%M %p')}</li>
                <li><strong>Location:</strong> {event.location}</li>
            </ul>
            <p>We look forward to seeing you!</p>
            <p>Best regards,<br>Event Management Team</p>
            """
            
            plain_message = f"""
            Event Reminder
            
            Dear {registration.user.first_name or registration.user.username},
            
            This is a reminder that you are registered for the following event tomorrow:
            
            Event: {event.title}
            Date: {event.date.strftime('%B %d, %Y at %I:%M %p')}
            Location: {event.location}
            
            We look forward to seeing you!
            
            Best regards,
            Event Management Team
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[registration.user.email],
                html_message=html_message,
                fail_silently=True,
            )
        
        return f"Reminder emails sent for event {event.title}"
    
    except Event.DoesNotExist:
        return f"Event with id {event_id} not found"
    except Exception as e:
        return f"Error sending reminder emails: {str(e)}"