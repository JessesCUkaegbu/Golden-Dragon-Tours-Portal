from django.urls import path
from .api_views import TicketListCreateAPIView, TicketDetailAPIView, DownloadTicketPDFAPIView

urlpatterns = [
    path("", TicketListCreateAPIView.as_view(), name="api_ticket_list"),
    path("<int:pk>/", TicketDetailAPIView.as_view(), name="api_ticket_detail"),
    path("<int:pk>/download/", DownloadTicketPDFAPIView.as_view(), name="api_download_ticket"),
]
