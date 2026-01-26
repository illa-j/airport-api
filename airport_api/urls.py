from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path("api/airport/", include("airport_service.urls")),
        path("api/user/", include("user.urls")),
        path("api/doc/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/doc/swagger/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "api/doc/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + debug_toolbar_urls()
)
