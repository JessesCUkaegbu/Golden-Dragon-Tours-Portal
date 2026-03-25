from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.PortalLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-ticket/', views.create_ticket, name='create_ticket'),
    path('ticket-success/<int:ticket_id>/', views.ticket_success, name='ticket_success'),
]
