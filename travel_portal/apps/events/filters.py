import django_filters
from .models import Event


class EventFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    location = django_filters.CharFilter(lookup_expr="icontains")
    min_price = django_filters.NumberFilter(field_name="ticket_price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="ticket_price", lookup_expr="lte")
    date_from = django_filters.DateFilter(field_name="event_date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="event_date", lookup_expr="lte")

    class Meta:
        model = Event
        fields = ["name", "location", "min_price", "max_price", "date_from", "date_to", "is_active"]
