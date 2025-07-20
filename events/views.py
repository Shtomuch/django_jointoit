from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from .models import Event, EventRegistration
from .serializers import (
    EventListSerializer,
    EventDetailSerializer,
    EventCreateUpdateSerializer,
    EventRegistrationSerializer
)
from .filters import EventFilter
from .tasks import send_registration_email, send_cancellation_email


class IsOrganizerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.organizer == request.user


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.select_related('organizer').annotate(
        attendees_count=Count('registrations', filter=Q(registrations__is_cancelled=False))
    ).order_by('date')
    filter_class = EventFilter
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['date', 'created_at', 'title']
    permission_classes = [IsAuthenticated, IsOrganizerOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EventCreateUpdateSerializer
        return EventDetailSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'upcoming']:
            return [AllowAny()]
        return [IsAuthenticated(), IsOrganizerOrReadOnly()]

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_events(self, request):
        events = self.get_queryset().filter(organizer=request.user)
        page = self.paginate_queryset(events)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def upcoming(self, request):
        events = self.get_queryset().filter(
            date__gte=timezone.now(),
            is_active=True
        )
        page = self.paginate_queryset(events)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def register(self, request, pk=None):
        event = self.get_object()
        
        if event.is_past:
            return Response(
                {"detail": "Cannot register for past events."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not event.is_active:
            return Response(
                {"detail": "This event is not active."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if event.max_attendees and event.attendees_count >= event.max_attendees:
            return Response(
                {"detail": "This event is full."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        registration, created = EventRegistration.objects.get_or_create(
            user=request.user,
            event=event,
            defaults={'is_cancelled': False}
        )
        
        if not created and not registration.is_cancelled:
            return Response(
                {"detail": "You are already registered for this event."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not created and registration.is_cancelled:
            registration.is_cancelled = False
            registration.cancelled_at = None
            registration.save()
        
        # Send registration email asynchronously
        send_registration_email.delay(registration.id)
        
        serializer = EventRegistrationSerializer(registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unregister(self, request, pk=None):
        event = self.get_object()
        
        try:
            registration = EventRegistration.objects.get(
                user=request.user,
                event=event,
                is_cancelled=False
            )
        except EventRegistration.DoesNotExist:
            return Response(
                {"detail": "You are not registered for this event."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        registration.cancel()
        
        # Send cancellation email asynchronously
        send_cancellation_email.delay(registration.id)
        
        return Response(
            {"detail": "Successfully unregistered from the event."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def attendees(self, request, pk=None):
        event = self.get_object()
        
        if event.organizer != request.user:
            return Response(
                {"detail": "Only the organizer can view attendees."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        registrations = event.registrations.filter(
            is_cancelled=False
        ).select_related('user')
        
        page = self.paginate_queryset(registrations)
        if page is not None:
            serializer = EventRegistrationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = EventRegistrationSerializer(registrations, many=True)
        return Response(serializer.data)


class MyRegistrationsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EventRegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EventRegistration.objects.filter(
            user=self.request.user
        ).select_related('event', 'event__organizer').order_by('-registered_at')

    @action(detail=False, methods=['get'])
    def active(self, request):
        registrations = self.get_queryset().filter(
            is_cancelled=False,
            event__date__gte=timezone.now()
        )
        page = self.paginate_queryset(registrations)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(registrations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def past(self, request):
        registrations = self.get_queryset().filter(
            is_cancelled=False,
            event__date__lt=timezone.now()
        )
        page = self.paginate_queryset(registrations)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(registrations, many=True)
        return Response(serializer.data)
