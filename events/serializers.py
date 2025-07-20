from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Event, EventRegistration


class EventOrganizerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class EventListSerializer(serializers.ModelSerializer):
    organizer = EventOrganizerSerializer(read_only=True)
    attendees_count = serializers.IntegerField(read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    available_spots = serializers.IntegerField(read_only=True)
    is_registered = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'date', 'location', 'organizer',
            'attendees_count', 'is_past', 'available_spots',
            'max_attendees', 'is_active', 'is_registered'
        ]

    def get_is_registered(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.registrations.filter(
                user=request.user,
                is_cancelled=False
            ).exists()
        return False


class EventDetailSerializer(serializers.ModelSerializer):
    organizer = EventOrganizerSerializer(read_only=True)
    attendees_count = serializers.IntegerField(read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    available_spots = serializers.IntegerField(read_only=True)
    is_registered = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_registered(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.registrations.filter(
                user=request.user,
                is_cancelled=False
            ).exists()
        return False


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'date', 'location',
            'max_attendees', 'is_active'
        ]

    def validate_date(self, value):
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Event date cannot be in the past.")
        return value


class EventRegistrationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_date = serializers.DateTimeField(source='event.date', read_only=True)

    class Meta:
        model = EventRegistration
        fields = [
            'id', 'user', 'event', 'event_title', 'event_date',
            'registered_at', 'is_cancelled', 'cancelled_at'
        ]
        read_only_fields = ['id', 'registered_at', 'cancelled_at']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']