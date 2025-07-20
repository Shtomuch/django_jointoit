from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from .models import Event, EventRegistration


class EventModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            date=timezone.now() + timedelta(days=7),
            location='Test Location',
            organizer=self.user,
            max_attendees=50
        )

    def test_event_creation(self):
        self.assertEqual(self.event.title, 'Test Event')
        self.assertTrue(self.event.is_active)
        self.assertFalse(self.event.is_past)

    def test_event_str(self):
        self.assertEqual(str(self.event), 'Test Event')

    def test_available_spots(self):
        self.assertEqual(self.event.available_spots, 50)
        
        # Create a registration
        EventRegistration.objects.create(
            user=self.user,
            event=self.event
        )
        self.assertEqual(self.event.available_spots, 49)


class EventAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

    def test_list_events(self):
        response = self.client.get('/api/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_event_authenticated(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'New Event',
            'description': 'New Description',
            'date': (timezone.now() + timedelta(days=10)).isoformat(),
            'location': 'New Location',
            'max_attendees': 100
        }
        response = self.client.post('/api/events/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.count(), 1)

    def test_create_event_unauthenticated(self):
        data = {
            'title': 'New Event',
            'description': 'New Description',
            'date': (timezone.now() + timedelta(days=10)).isoformat(),
            'location': 'New Location'
        }
        response = self.client.post('/api/events/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_for_event(self):
        event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            date=timezone.now() + timedelta(days=7),
            location='Test Location',
            organizer=self.user,
            max_attendees=50
        )
        
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(f'/api/events/{event.id}/register/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            EventRegistration.objects.filter(
                user=self.other_user,
                event=event
            ).exists()
        )

    def test_cannot_register_twice(self):
        event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            date=timezone.now() + timedelta(days=7),
            location='Test Location',
            organizer=self.user,
            max_attendees=50
        )
        
        self.client.force_authenticate(user=self.other_user)
        self.client.post(f'/api/events/{event.id}/register/')
        response = self.client.post(f'/api/events/{event.id}/register/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthenticationTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_registration(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password2': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_login(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
