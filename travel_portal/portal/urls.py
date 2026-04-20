from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('events/', views.event_list, name='event_list'),
    path('register/', views.register_view, name='register'),
    path('login/', views.PortalLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('event-studio/', views.event_studio, name='event_studio'),
    path('create-ticket/', views.create_ticket, name='create_ticket'),
    path('create-event/', views.create_event, name='create_event'),
    path('event/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('event/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    path('ticket-success/<int:ticket_id>/', views.ticket_success, name='ticket_success'),
    path('tickets/<int:ticket_id>/download-pdf/', views.download_ticket_pdf, name='download_ticket_pdf'),
    
    # Subscription
    path('pricing/', views.pricing_view, name='pricing'),
    path('subscription/checkout/<str:plan>/', views.create_checkout_session, name='checkout'),
    path('subscription/success/', views.subscription_success, name='subscription_success'),
    path('subscription/cancel/', views.cancel_subscription, name='cancel_subscription'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
]
