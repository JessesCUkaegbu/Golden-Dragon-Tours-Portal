from django.urls import path
from . import views
from .webhook import stripe_webhook

urlpatterns = [
    path('pricing/', views.pricing_view, name='pricing'),
    path('subscription/checkout/<str:plan>/', views.create_checkout_session, name='checkout'),
    path('subscription/success/', views.subscription_success, name='subscription_success'),
    path('subscription/cancel/', views.cancel_subscription, name='cancel_subscription'),
    path('stripe/webhook/', stripe_webhook, name='stripe_webhook'),
]
