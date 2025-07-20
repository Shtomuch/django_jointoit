from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
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


@extend_schema_view(
    list=extend_schema(
        summary='List all events',
        description='Get a paginated list of all events with optional filtering',
        parameters=[
            OpenApiParameter(
                name='page',
                type=int,
                description='Page number',
                required=False
            ),
            OpenApiParameter(
                name='search',
                type=str,
                description='Search in title, description, and location',
                required=False
            ),
            OpenApiParameter(
                name='organizer',
                type=int,
                description='Filter by organizer ID',
                required=False
            ),
            OpenApiParameter(
                name='date_after',
                type=str,
                description='Filter events after this date (YYYY-MM-DD)',
                required=False
            ),
            OpenApiParameter(
                name='date_before',
                type=str,
                description='Filter events before this date (YYYY-MM-DD)',
                required=False
            ),
            OpenApiParameter(
                name='is_active',
                type=bool,
                description='Filter by active status',
                required=False
            ),
            OpenApiParameter(
                name='ordering',
                type=str,
                description='Order by: date, -date, created_at, -created_at, title, -title',
                required=False
            )
        ],
        responses={
            200: {
                'description': 'Events retrieved successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'count': 100,
                            'next': 'http://api.example.com/events/?page=2',
                            'previous': None,
                            'results': [
                                {
                                    'id': 1,
                                    'title': 'Django Conference 2024',
                                    'description': 'Annual Django developers conference',
                                    'date': '2024-06-15T09:00:00Z',
                                    'location': 'San Francisco, CA',
                                    'organizer_name': 'John Doe',
                                    'attendees_count': 45,
                                    'available_spots': 55,
                                    'is_active': True,
                                    'is_past': False
                                }
                            ]
                        }
                    }
                }
            }
        }
    ),
    create=extend_schema(
        summary='Create a new event',
        description='Create a new event. The authenticated user will be set as the organizer.',
        request={
            'application/json': {
                'example': {
                    'title': 'Python Workshop',
                    'description': 'Hands-on Python programming workshop for beginners',
                    'date': '2024-07-20T14:00:00Z',
                    'location': 'Tech Hub, New York',
                    'max_attendees': 30
                }
            }
        },
        responses={
            201: {
                'description': 'Event created successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'id': 2,
                            'title': 'Python Workshop',
                            'description': 'Hands-on Python programming workshop for beginners',
                            'date': '2024-07-20T14:00:00Z',
                            'location': 'Tech Hub, New York',
                            'organizer': 1,
                            'organizer_name': 'Jane Smith',
                            'max_attendees': 30,
                            'attendees_count': 0,
                            'available_spots': 30,
                            'is_active': True,
                            'is_past': False,
                            'created_at': '2024-01-10T10:00:00Z',
                            'updated_at': '2024-01-10T10:00:00Z'
                        }
                    }
                }
            },
            400: {
                'description': 'Validation error',
                'content': {
                    'application/json': {
                        'example': {
                            'title': ['This field is required.'],
                            'date': ['Datetime has wrong format.']
                        }
                    }
                }
            },
            401: {
                'description': 'Authentication required'
            }
        }
    ),
    retrieve=extend_schema(
        summary='Get event details',
        description='Retrieve detailed information about a specific event',
        responses={
            200: {
                'description': 'Event details retrieved successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'id': 1,
                            'title': 'Django Conference 2024',
                            'description': 'Annual Django developers conference',
                            'date': '2024-06-15T09:00:00Z',
                            'location': 'San Francisco, CA',
                            'organizer': 1,
                            'organizer_name': 'John Doe',
                            'max_attendees': 100,
                            'attendees_count': 45,
                            'available_spots': 55,
                            'is_active': True,
                            'is_past': False,
                            'created_at': '2024-01-01T10:00:00Z',
                            'updated_at': '2024-01-05T15:30:00Z'
                        }
                    }
                }
            },
            404: {
                'description': 'Event not found'
            }
        }
    ),
    update=extend_schema(
        summary='Update event',
        description='Update all fields of an event. Only the organizer can update their events.',
        request={
            'application/json': {
                'example': {
                    'title': 'Django Conference 2024 - Updated',
                    'description': 'Updated description',
                    'date': '2024-06-16T09:00:00Z',
                    'location': 'San Francisco, CA - Main Hall',
                    'max_attendees': 150
                }
            }
        },
        responses={
            200: {
                'description': 'Event updated successfully'
            },
            400: {
                'description': 'Validation error'
            },
            401: {
                'description': 'Authentication required'
            },
            403: {
                'description': 'Only the organizer can update this event'
            },
            404: {
                'description': 'Event not found'
            }
        }
    ),
    partial_update=extend_schema(
        summary='Partially update event',
        description='Update specific fields of an event. Only the organizer can update their events.',
        request={
            'application/json': {
                'example': {
                    'max_attendees': 200,
                    'location': 'Updated location'
                }
            }
        },
        responses={
            200: {
                'description': 'Event updated successfully'
            },
            400: {
                'description': 'Validation error'
            },
            401: {
                'description': 'Authentication required'
            },
            403: {
                'description': 'Only the organizer can update this event'
            },
            404: {
                'description': 'Event not found'
            }
        }
    ),
    destroy=extend_schema(
        summary='Delete event',
        description='Delete an event. Only the organizer can delete their events.',
        responses={
            204: {
                'description': 'Event deleted successfully'
            },
            401: {
                'description': 'Authentication required'
            },
            403: {
                'description': 'Only the organizer can delete this event'
            },
            404: {
                'description': 'Event not found'
            }
        }
    )
)
@extend_schema(tags=['Events'])
class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing events.
    
    Provides CRUD operations for events with role-based permissions.
    Organizers can manage their own events, while others can view and register.
    """
    queryset = Event.objects.select_related('organizer').order_by('date')
    filterset_class = EventFilter
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['date', 'created_at', 'title']

    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EventCreateUpdateSerializer
        return EventDetailSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'upcoming']:
            return [AllowAny()]
        elif self.action in ['register', 'unregister', 'my_events', 'attendees']:
            return [IsAuthenticated()]
        elif self.action in ['create']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOrganizerOrReadOnly()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @extend_schema(
        summary='Get my organized events',
        description='Get all events organized by the authenticated user',
        responses={
            200: {
                'description': 'List of events organized by the user',
                'content': {
                    'application/json': {
                        'example': {
                            'count': 5,
                            'results': [
                                {
                                    'id': 1,
                                    'title': 'My Workshop',
                                    'date': '2024-06-15T09:00:00Z',
                                    'attendees_count': 20
                                }
                            ]
                        }
                    }
                }
            },
            401: {
                'description': 'Authentication required'
            }
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_events(self, request):
        events = self.get_queryset().filter(organizer=request.user)
        page = self.paginate_queryset(events)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary='Get upcoming events',
        description='Get all active events scheduled for the future',
        responses={
            200: {
                'description': 'List of upcoming events',
                'content': {
                    'application/json': {
                        'example': {
                            'count': 25,
                            'results': [
                                {
                                    'id': 3,
                                    'title': 'Tech Meetup',
                                    'date': '2024-03-20T18:00:00Z',
                                    'location': 'Downtown Tech Center',
                                    'available_spots': 15
                                }
                            ]
                        }
                    }
                }
            }
        }
    )
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

    @extend_schema(
        summary='Register for an event',
        description='Register the authenticated user for this event',
        request=None,
        responses={
            201: {
                'description': 'Successfully registered for the event',
                'content': {
                    'application/json': {
                        'example': {
                            'id': 10,
                            'user': 2,
                            'event': 1,
                            'registered_at': '2024-01-10T15:30:00Z',
                            'is_cancelled': False
                        }
                    }
                }
            },
            400: {
                'description': 'Registration failed',
                'content': {
                    'application/json': {
                        'examples': {
                            'already_registered': {
                                'value': {'detail': 'You are already registered for this event.'}
                            },
                            'event_full': {
                                'value': {'detail': 'This event is full.'}
                            },
                            'past_event': {
                                'value': {'detail': 'Cannot register for past events.'}
                            },
                            'inactive_event': {
                                'value': {'detail': 'This event is not active.'}
                            }
                        }
                    }
                }
            },
            401: {
                'description': 'Authentication required'
            },
            404: {
                'description': 'Event not found'
            }
        }
    )
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

    @extend_schema(
        summary='Unregister from an event',
        description='Cancel registration for this event',
        request=None,
        responses={
            200: {
                'description': 'Successfully unregistered from the event',
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'Successfully unregistered from the event.'
                        }
                    }
                }
            },
            400: {
                'description': 'Not registered for this event',
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'You are not registered for this event.'
                        }
                    }
                }
            },
            401: {
                'description': 'Authentication required'
            },
            404: {
                'description': 'Event not found'
            }
        }
    )
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

    @extend_schema(
        summary='Get event attendees',
        description='Get list of registered attendees. Only the event organizer can access this.',
        responses={
            200: {
                'description': 'List of event attendees',
                'content': {
                    'application/json': {
                        'example': {
                            'count': 15,
                            'results': [
                                {
                                    'id': 5,
                                    'user': 3,
                                    'event': 1,
                                    'registered_at': '2024-01-05T10:00:00Z',
                                    'is_cancelled': False
                                }
                            ]
                        }
                    }
                }
            },
            401: {
                'description': 'Authentication required'
            },
            403: {
                'description': 'Only the organizer can view attendees',
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'Only the organizer can view attendees.'
                        }
                    }
                }
            },
            404: {
                'description': 'Event not found'
            }
        }
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


@extend_schema_view(
    list=extend_schema(
        tags=['My Registrations'],
        summary='Get my event registrations',
        description='Get all event registrations for the authenticated user',
        responses={
            200: {
                'description': 'List of user registrations',
                'content': {
                    'application/json': {
                        'example': {
                            'count': 10,
                            'results': [
                                {
                                    'id': 1,
                                    'event': {
                                        'id': 1,
                                        'title': 'Django Conference',
                                        'date': '2024-06-15T09:00:00Z'
                                    },
                                    'registered_at': '2024-01-01T10:00:00Z',
                                    'is_cancelled': False
                                }
                            ]
                        }
                    }
                }
            },
            401: {
                'description': 'Authentication required'
            }
        }
    ),
    retrieve=extend_schema(
        tags=['My Registrations'],
        summary='Get registration details',
        description='Get details of a specific registration',
        responses={
            200: {
                'description': 'Registration details'
            },
            401: {
                'description': 'Authentication required'
            },
            404: {
                'description': 'Registration not found'
            }
        }
    )
)
class MyRegistrationsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EventRegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EventRegistration.objects.filter(
            user=self.request.user
        ).select_related('event', 'event__organizer').order_by('-registered_at')

    @extend_schema(
        tags=['My Registrations'],
        summary='Get active registrations',
        description='Get all active (not cancelled) registrations for upcoming events',
        responses={
            200: {
                'description': 'List of active registrations',
                'content': {
                    'application/json': {
                        'example': {
                            'count': 3,
                            'results': [
                                {
                                    'id': 2,
                                    'event': {
                                        'id': 5,
                                        'title': 'Python Workshop',
                                        'date': '2024-04-10T14:00:00Z'
                                    },
                                    'registered_at': '2024-01-15T12:00:00Z'
                                }
                            ]
                        }
                    }
                }
            },
            401: {
                'description': 'Authentication required'
            }
        }
    )
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

    @extend_schema(
        tags=['My Registrations'],
        summary='Get past registrations',
        description='Get all registrations for past events',
        responses={
            200: {
                'description': 'List of past registrations',
                'content': {
                    'application/json': {
                        'example': {
                            'count': 7,
                            'results': [
                                {
                                    'id': 8,
                                    'event': {
                                        'id': 2,
                                        'title': 'Tech Conference 2023',
                                        'date': '2023-11-15T09:00:00Z'
                                    },
                                    'registered_at': '2023-10-01T10:00:00Z'
                                }
                            ]
                        }
                    }
                }
            },
            401: {
                'description': 'Authentication required'
            }
        }
    )
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
