from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.shortcuts import render


def home(request):
    return render(request, "frontend/home.html")


def favicon(request):
    # Return an empty 204 so browsers stop logging 404s for favicon.ico
    return HttpResponse(status=204)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("favicon.ico", favicon),
    path("", home, name="home"),
    path("", include("apps.accounts.urls")),
    path("", include("apps.tickets.urls")),
    path("", include("apps.events.urls")),
    path("", include("apps.subscriptions.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
