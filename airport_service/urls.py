from django.urls import path, include
from rest_framework import routers

from airport_service.views import (
    AirportViewSet,
    CountryViewSet,
    CityViewSet
)

router = routers.DefaultRouter()
router.register(r'countries', CountryViewSet)
router.register(r'cities', CityViewSet)
router.register(r'airports', AirportViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "airport_service"
