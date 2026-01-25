from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport_service.models import (
    Airport,
    City,
    Country,
    Route,
)
from airport_service.serializers import RouteListSerializer, RouteDetailSerializer

ROUTE_URL = reverse("airport_service:route-list")


def detail_url(route_id):
    return reverse("airport_service:route-detail", args=[route_id])


def sample_country(**params):
    defaults = {"name": "Sample country"}
    defaults.update(params)

    return Country.objects.create(**defaults)


def sample_city(**params):
    defaults = {"name": "Sample city"}
    defaults.update(params)

    return City.objects.create(**defaults)


def sample_airport(**params):
    defaults = {"name": "Sample Airport", "code": "SAM"}
    defaults.update(params)

    return Airport.objects.create(**defaults)


def sample_route(**params):
    defaults = {"distance": 1000}
    defaults.update(params)

    return Route.objects.create(**defaults)


class UnauthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ROUTE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_routes(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        sample_route(source_id=airport1.id, destination_id=airport2.id, distance=500)
        sample_route(source_id=airport2.id, destination_id=airport1.id, distance=500)

        res = self.client.get(ROUTE_URL)

        routes = Route.objects.order_by("id")
        serializer = RouteListSerializer(routes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_routes_by_source_city(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)
        city3 = sample_city(name="Berlin", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )
        airport3 = sample_airport(name="Brandenburg", code="BER", city_id=city3.id)

        route1 = sample_route(
            source_id=airport1.id, destination_id=airport2.id, distance=500
        )
        route2 = sample_route(
            source_id=airport3.id, destination_id=airport2.id, distance=1000
        )

        res = self.client.get(ROUTE_URL, {"source_city": "London"})

        serializer1 = RouteListSerializer(route1)
        serializer2 = RouteListSerializer(route2)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_filter_routes_by_destination_city(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)
        city3 = sample_city(name="Berlin", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )
        airport3 = sample_airport(name="Brandenburg", code="BER", city_id=city3.id)

        route1 = sample_route(
            source_id=airport1.id, destination_id=airport2.id, distance=500
        )
        route2 = sample_route(
            source_id=airport1.id, destination_id=airport3.id, distance=1000
        )

        res = self.client.get(ROUTE_URL, {"destination_city": "Berlin"})

        serializer1 = RouteListSerializer(route1)
        serializer2 = RouteListSerializer(route2)

        self.assertNotIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])

    def test_filter_routes_by_distance(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)
        city3 = sample_city(name="Berlin", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )
        airport3 = sample_airport(name="Brandenburg", code="BER", city_id=city3.id)

        route1 = sample_route(
            source_id=airport1.id, destination_id=airport2.id, distance=500
        )
        route2 = sample_route(
            source_id=airport1.id, destination_id=airport3.id, distance=1000
        )

        res = self.client.get(ROUTE_URL, {"distance": "500"})

        serializer1 = RouteListSerializer(route1)
        serializer2 = RouteListSerializer(route2)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_retrieve_route_detail(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(
            source_id=airport1.id, destination_id=airport2.id, distance=500
        )

        url = detail_url(route.id)
        res = self.client.get(url)

        serializer = RouteDetailSerializer(route)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_route_forbidden(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        payload = {"source": airport1.id, "destination": airport2.id, "distance": 500}
        res = self.client.post(ROUTE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_route(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        payload = {"source": airport1.id, "destination": airport2.id, "distance": 500}
        res = self.client.post(ROUTE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        route = Route.objects.get(id=res.data["id"])

        self.assertEqual(airport1, route.source)
        self.assertEqual(airport2, route.destination)
        self.assertEqual(payload["distance"], route.distance)

    def test_create_route_with_same_source_and_destination_invalid(self):
        country = sample_country()
        city = sample_city(name="London", country_id=country.id)

        airport = sample_airport(name="Heathrow", code="LHR", city_id=city.id)

        payload = {"source": airport.id, "destination": airport.id, "distance": 500}
        res = self.client.post(ROUTE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_duplicate_route_invalid(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        sample_route(source_id=airport1.id, destination_id=airport2.id, distance=500)

        payload = {"source": airport1.id, "destination": airport2.id, "distance": 600}
        res = self.client.post(ROUTE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_route(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(
            source_id=airport1.id, destination_id=airport2.id, distance=500
        )

        payload = {"source": airport1.id, "destination": airport2.id, "distance": 600}

        url = detail_url(route.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        route.refresh_from_db()
        self.assertEqual(route.distance, payload["distance"])

    def test_partial_update_route(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(
            source_id=airport1.id, destination_id=airport2.id, distance=500
        )

        payload = {"distance": 550}

        url = detail_url(route.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        route.refresh_from_db()
        self.assertEqual(route.distance, payload["distance"])
        self.assertEqual(route.source, airport1)
        self.assertEqual(route.destination, airport2)

    def test_delete_route(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(
            source_id=airport1.id, destination_id=airport2.id, distance=500
        )

        url = detail_url(route.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Route.objects.filter(id=route.id).exists())
