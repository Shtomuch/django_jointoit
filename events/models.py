from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone


class Event(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    date = models.DateTimeField(db_index=True)
    location = models.CharField(max_length=300)
    organizer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='organized_events'
    )
    max_attendees = models.IntegerField(
        validators=[MinValueValidator(1)],
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date']
        indexes = [
            models.Index(fields=['date', 'is_active']),
            models.Index(fields=['organizer', 'date']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_past(self):
        return self.date < timezone.now()

    @property
    def attendees_count(self):
        return self.registrations.filter(is_cancelled=False).count()

    @property
    def available_spots(self):
        if self.max_attendees:
            return max(0, self.max_attendees - self.attendees_count)
        return None


class EventRegistration(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='event_registrations'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='registrations'
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    is_cancelled = models.BooleanField(default=False)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'event']
        indexes = [
            models.Index(fields=['event', 'is_cancelled']),
            models.Index(fields=['user', 'is_cancelled']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"

    def cancel(self):
        self.is_cancelled = True
        self.cancelled_at = timezone.now()
        self.save()
