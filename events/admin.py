from django.contrib import admin
from django.db import models
from django.db.models import Count
from .models import Event, EventRegistration


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'location', 'organizer', 'is_active', 'attendees_count', 'max_attendees']
    list_filter = ['date', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'location', 'organizer__username']
    readonly_fields = ['created_at', 'updated_at', 'attendees_count']
    date_hierarchy = 'date'
    ordering = ['-date']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _attendees_count=Count('registrations', filter=models.Q(registrations__is_cancelled=False))
        )
        return queryset

    def attendees_count(self, obj):
        return obj._attendees_count
    attendees_count.short_description = 'Attendees'
    attendees_count.admin_order_field = '_attendees_count'


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'registered_at', 'is_cancelled']
    list_filter = ['is_cancelled', 'registered_at', 'event__date']
    search_fields = ['user__username', 'user__email', 'event__title']
    readonly_fields = ['registered_at', 'cancelled_at']
    date_hierarchy = 'registered_at'
    ordering = ['-registered_at']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'event', 'event__organizer')
