from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from airport_service.models import (
    Flight,
    Route,
    Airplane,
    AirplaneType,
    Airport,
    City,
    Country,
)
from airport_service.serializers import FlightListSerializer, FlightDetailSerializer

FLIGHT_URL = reverse("airport_service:flight-list")


def detail_url(flight_id):
    return reverse("airport_service:flight-detail", args=[flight_id])


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


def sample_airplane_type(**params):
    defaults = {"name": "Sample Airplane Type"}
    defaults.update(params)

    return AirplaneType.objects.create(**defaults)


def sample_airplane(**params):
    defaults = {"name": "Sample Airplane", "rows": 30, "seats_in_row": 6}
    defaults.update(params)

    return Airplane.objects.create(**defaults)


def sample_flight(**params):
    defaults = {
        "departure_time": timezone.make_aware(datetime(2024, 1, 15, 10, 0)),
        "arrival_time": timezone.make_aware(datetime(2024, 1, 15, 12, 0)),
    }
    defaults.update(params)

    return Flight.objects.create(**defaults)


class UnauthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(FLIGHT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_flights(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(source_id=airport1.id, destination_id=airport2.id)

        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type_id=airplane_type.id)

        sample_flight(route_id=route.id, airplane_id=airplane.id)
        sample_flight(
            route_id=route.id,
            airplane_id=airplane.id,
            departure_time=timezone.make_aware(datetime(2024, 1, 16, 10, 0)),
            arrival_time=timezone.make_aware(datetime(2024, 1, 16, 12, 0)),
        )

        res = self.client.get(FLIGHT_URL)

        for flight in res.data["results"]:
            del flight["tickets_available"]

        flights = Flight.objects.order_by("id")
        serializer = FlightListSerializer(flights, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_flights_by_route_from(self):
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

        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type_id=airplane_type.id)

        flight1 = sample_flight(route_id=route1.id, airplane_id=airplane.id)
        flight2 = sample_flight(
            route_id=route2.id,
            airplane_id=airplane.id,
            departure_time=timezone.make_aware(datetime(2024, 1, 16, 10, 0)),
            arrival_time=timezone.make_aware(datetime(2024, 1, 16, 12, 0)),
        )

        res = self.client.get(FLIGHT_URL, {"route_from": "London"})

        flight_ids = [flight["id"] for flight in res.data["results"]]

        self.assertIn(flight1.id, flight_ids)
        self.assertNotIn(flight2.id, flight_ids)

    def test_filter_flights_by_route_to(self):
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

        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type_id=airplane_type.id)

        flight1 = sample_flight(route_id=route1.id, airplane_id=airplane.id)
        flight2 = sample_flight(
            route_id=route2.id,
            airplane_id=airplane.id,
            departure_time=timezone.make_aware(datetime(2024, 1, 16, 10, 0)),
            arrival_time=timezone.make_aware(datetime(2024, 1, 16, 12, 0)),
        )

        res = self.client.get(FLIGHT_URL, {"route_to": "Berlin"})

        flight_ids = [flight["id"] for flight in res.data["results"]]

        self.assertIn(flight2.id, flight_ids)
        self.assertNotIn(flight1.id, flight_ids)

    def test_filter_flights_by_departure_date(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(source_id=airport1.id, destination_id=airport2.id)

        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type_id=airplane_type.id)

        today = timezone.make_aware(datetime(2024, 1, 15, 10, 0))
        tomorrow = today + timedelta(days=1)

        flight1 = sample_flight(
            route_id=route.id,
            airplane_id=airplane.id,
            departure_time=today,
            arrival_time=today + timedelta(hours=2),
        )
        flight2 = sample_flight(
            route_id=route.id,
            airplane_id=airplane.id,
            departure_time=tomorrow,
            arrival_time=tomorrow + timedelta(hours=2),
        )

        res = self.client.get(FLIGHT_URL, {"departure": today.date().isoformat()})

        flight_ids = [flight["id"] for flight in res.data["results"]]

        self.assertIn(flight1.id, flight_ids)
        self.assertNotIn(flight2.id, flight_ids)

    def test_filter_flights_by_arrival_date(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(source_id=airport1.id, destination_id=airport2.id)

        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type_id=airplane_type.id)

        today = timezone.make_aware(datetime(2024, 1, 15, 10, 0))
        tomorrow = today + timedelta(days=1)

        flight1 = sample_flight(
            route_id=route.id,
            airplane_id=airplane.id,
            departure_time=today,
            arrival_time=today + timedelta(hours=2),
        )
        flight2 = sample_flight(
            route_id=route.id,
            airplane_id=airplane.id,
            departure_time=today + timedelta(hours=20),
            arrival_time=tomorrow + timedelta(hours=2),
        )

        res = self.client.get(FLIGHT_URL, {"arrival": tomorrow.date().isoformat()})

        flight_ids = [flight["id"] for flight in res.data["results"]]

        self.assertIn(flight2.id, flight_ids)
        self.assertNotIn(flight1.id, flight_ids)

    def test_retrieve_flight_detail(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(source_id=airport1.id, destination_id=airport2.id)

        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type_id=airplane_type.id)

        flight = sample_flight(route_id=route.id, airplane_id=airplane.id)

        url = detail_url(flight.id)
        res = self.client.get(url)

        serializer = FlightDetailSerializer(flight)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_flight_forbidden(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(source_id=airport1.id, destination_id=airport2.id)

        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type_id=airplane_type.id)

        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "departure_time": timezone.make_aware(
                datetime(2024, 1, 15, 10, 0)
            ).isoformat(),
            "arrival_time": timezone.make_aware(
                datetime(2024, 1, 15, 12, 0)
            ).isoformat(),
        }
        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_flight(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(source_id=airport1.id, destination_id=airport2.id)

        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type_id=airplane_type.id)

        departure_time = timezone.make_aware(datetime(2024, 1, 15, 10, 0))
        arrival_time = departure_time + timedelta(hours=2)

        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "departure_time": departure_time.isoformat(),
            "arrival_time": arrival_time.isoformat(),
        }
        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        flight = Flight.objects.get(id=res.data["id"])

        self.assertEqual(flight.route, route)
        self.assertEqual(flight.airplane, airplane)

    def test_create_flight_with_invalid_times(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(source_id=airport1.id, destination_id=airport2.id)

        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type_id=airplane_type.id)

        departure_time = timezone.make_aware(datetime(2024, 1, 15, 10, 0))
        arrival_time = departure_time - timedelta(hours=2)

        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "departure_time": departure_time.isoformat(),
            "arrival_time": arrival_time.isoformat(),
        }
        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_flight_with_same_departure_and_arrival_time(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(source_id=airport1.id, destination_id=airport2.id)

        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type_id=airplane_type.id)

        same_time = timezone.make_aware(datetime(2024, 1, 15, 10, 0))

        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "departure_time": same_time.isoformat(),
            "arrival_time": same_time.isoformat(),
        }
        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_flight(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(source_id=airport1.id, destination_id=airport2.id)

        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type_id=airplane_type.id)

        flight = sample_flight(route_id=route.id, airplane_id=airplane.id)

        new_departure = timezone.make_aware(datetime(2024, 1, 16, 10, 0))
        new_arrival = new_departure + timedelta(hours=3)

        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "departure_time": new_departure.isoformat(),
            "arrival_time": new_arrival.isoformat(),
        }

        url = detail_url(flight.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        flight.refresh_from_db()
        self.assertEqual(
            flight.departure_time.replace(microsecond=0),
            new_departure.replace(microsecond=0),
        )
        self.assertEqual(
            flight.arrival_time.replace(microsecond=0),
            new_arrival.replace(microsecond=0),
        )

    def test_partial_update_flight(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(source_id=airport1.id, destination_id=airport2.id)

        airplane_type = sample_airplane_type()
        airplane1 = sample_airplane(
            name="Airplane 1", airplane_type_id=airplane_type.id
        )
        airplane2 = sample_airplane(
            name="Airplane 2", airplane_type_id=airplane_type.id
        )

        departure_time = timezone.make_aware(datetime(2024, 1, 15, 10, 0))
        arrival_time = departure_time + timedelta(hours=2)

        flight = sample_flight(
            route_id=route.id,
            airplane_id=airplane1.id,
            departure_time=departure_time,
            arrival_time=arrival_time,
        )

        payload = {"airplane": airplane2.id}

        url = detail_url(flight.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        flight.refresh_from_db()
        self.assertEqual(flight.airplane, airplane2)
        self.assertEqual(flight.route, route)

    def test_delete_flight(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(source_id=airport1.id, destination_id=airport2.id)

        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type_id=airplane_type.id)

        flight = sample_flight(route_id=route.id, airplane_id=airplane.id)

        url = detail_url(flight.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Flight.objects.filter(id=flight.id).exists())
