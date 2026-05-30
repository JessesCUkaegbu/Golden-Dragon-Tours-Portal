from django.urls import path
from .api_views import RegisterAPIView, MeAPIView

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="api_register"),
    path("me/", MeAPIView.as_view(), name="api_me"),
]
