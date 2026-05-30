from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.event_list, name='event_list'),
    path('event-studio/', views.event_studio, name='event_studio'),
    path('create-event/', views.create_event, name='create_event'),
    path('event/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('event/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    path('event-studio/tickets/<int:ticket_id>/<str:status>/', views.update_event_ticket_status, name='update_event_ticket_status'),
]
