from rest_framework import generics, permissions
from .models import Event
from .serializers import EventSerializer


class EventListAPIView(generics.ListAPIView):
    """Public: list all active events."""
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Event.objects.filter(is_active=True).order_by("event_date", "-created_at")


class OrganizerEventListCreateAPIView(generics.ListCreateAPIView):
    """Organiser: list own events or create a new one."""
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Event.objects.filter(creator=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class OrganizerEventDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Organiser: retrieve, update, or delete an own event."""
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Event.objects.filter(creator=self.request.user)
