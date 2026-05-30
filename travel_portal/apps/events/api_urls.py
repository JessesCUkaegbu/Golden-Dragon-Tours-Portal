from django.urls import path
from .api_views import EventListAPIView, OrganizerEventListCreateAPIView, OrganizerEventDetailAPIView

urlpatterns = [
    path("", EventListAPIView.as_view(), name="api_event_list"),
    path("mine/", OrganizerEventListCreateAPIView.as_view(), name="api_my_events"),
    path("mine/<int:pk>/", OrganizerEventDetailAPIView.as_view(), name="api_event_detail"),
]
