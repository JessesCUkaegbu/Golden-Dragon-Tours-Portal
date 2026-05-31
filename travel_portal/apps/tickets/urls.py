from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-ticket/', views.create_ticket, name='create_ticket'),
    path('ticket-success/<int:ticket_id>/', views.ticket_success, name='ticket_success'),
    path('tickets/<int:ticket_id>/download-pdf/', views.download_ticket_pdf, name='download_ticket_pdf'),
    path('tickets/<int:ticket_id>/cancel/', views.cancel_ticket, name='cancel_ticket'),
]
