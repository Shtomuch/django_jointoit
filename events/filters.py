import django_filters
from django.utils import timezone
from .models import Event


class EventFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    location = django_filters.CharFilter(lookup_expr='icontains')
    date_from = django_filters.DateTimeFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='date', lookup_expr='lte')
    organizer = django_filters.NumberFilter(field_name='organizer__id')
    has_spots = django_filters.BooleanFilter(method='filter_has_spots')
    is_past = django_filters.BooleanFilter(method='filter_is_past')
    
    class Meta:
        model = Event
        fields = ['is_active', 'organizer']
    
    def filter_has_spots(self, queryset, name, value):
        if value:
            return queryset.extra(
                where=[
                    "max_attendees IS NULL OR max_attendees > (SELECT COUNT(*) FROM events_eventregistration WHERE event_id = events_event.id AND is_cancelled = FALSE)"
                ]
            )
        return queryset
    
    def filter_is_past(self, queryset, name, value):
        now = timezone.now()
        if value:
            return queryset.filter(date__lt=now)
        return queryset.filter(date__gte=now)