from django.urls import path, include
from rest_framework import routers

from airport_service.views import (
    AirportViewSet,
    CountryViewSet,
    CityViewSet,
    RouteViewSet,
    AirplaneViewSet,
    AirplaneTypeViewSet, CrewViewSet, FlightViewSet
)

router = routers.DefaultRouter()
router.register("countries", CountryViewSet)
router.register("cities", CityViewSet)
router.register("airports", AirportViewSet)
router.register("routes", RouteViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("airplane_types", AirplaneTypeViewSet)
router.register("crews", CrewViewSet)
router.register("flights", FlightViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "airport_service"
