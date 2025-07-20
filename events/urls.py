from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, MyRegistrationsViewSet

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')
router.register(r'my-registrations', MyRegistrationsViewSet, basename='my-registration')

urlpatterns = [
    path('', include(router.urls)),
]