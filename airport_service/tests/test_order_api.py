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
    Order,
    Ticket,
)
from airport_service.serializers import OrderListSerializer

ORDER_URL = reverse("airport_service:order-list")


def detail_url(order_id):
    return reverse("airport_service:order-detail", args=[order_id])


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


def sample_order(**params):
    defaults = {}
    defaults.update(params)

    return Order.objects.create(**defaults)


def sample_ticket(**params):
    defaults = {"row": 1, "seat": 1}
    defaults.update(params)

    return Ticket.objects.create(**defaults)


class UnauthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_orders(self):
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

        order1 = sample_order(user=self.user)
        order2 = sample_order(user=self.user)

        sample_ticket(flight_id=flight.id, order_id=order1.id, row=1, seat=1)
        sample_ticket(flight_id=flight.id, order_id=order2.id, row=1, seat=2)

        res = self.client.get(ORDER_URL)

        orders = Order.objects.filter(user=self.user).order_by("-created_at")
        serializer = OrderListSerializer(orders, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_retrieve_order_detail(self):
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

        order = sample_order(user=self.user)
        sample_ticket(flight_id=flight.id, order_id=order.id, row=1, seat=1)

        url = detail_url(order.id)
        res = self.client.get(url)

        serializer = OrderListSerializer(order)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_order_with_tickets(self):
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

        payload = {
            "tickets": [
                {"flight": flight.id, "row": 1, "seat": 1},
                {"flight": flight.id, "row": 1, "seat": 2},
            ]
        }

        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(id=res.data["id"])
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.tickets.count(), 2)

    def test_create_order_with_invalid_seat(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(source_id=airport1.id, destination_id=airport2.id)

        airplane_type = sample_airplane_type()
        airplane = sample_airplane(
            airplane_type_id=airplane_type.id, rows=10, seats_in_row=6
        )

        flight = sample_flight(route_id=route.id, airplane_id=airplane.id)

        payload = {"tickets": [{"flight": flight.id, "row": 1, "seat": 10}]}

        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_with_invalid_row(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )

        route = sample_route(source_id=airport1.id, destination_id=airport2.id)

        airplane_type = sample_airplane_type()
        airplane = sample_airplane(
            airplane_type_id=airplane_type.id, rows=10, seats_in_row=6
        )

        flight = sample_flight(route_id=route.id, airplane_id=airplane.id)

        payload = {"tickets": [{"flight": flight.id, "row": 15, "seat": 1}]}

        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_with_duplicate_ticket(self):
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

        existing_order = sample_order(user=self.user)
        sample_ticket(flight_id=flight.id, order_id=existing_order.id, row=1, seat=1)

        payload = {"tickets": [{"flight": flight.id, "row": 1, "seat": 1}]}

        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_with_multiple_flights(self):
        country = sample_country()
        city1 = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Paris", country_id=country.id)
        city3 = sample_city(name="Berlin", country_id=country.id)

        airport1 = sample_airport(name="Heathrow", code="LHR", city_id=city1.id)
        airport2 = sample_airport(
            name="Charles de Gaulle", code="CDG", city_id=city2.id
        )
        airport3 = sample_airport(name="Brandenburg", code="BER", city_id=city3.id)

        route1 = sample_route(source_id=airport1.id, destination_id=airport2.id)
        route2 = sample_route(
            source_id=airport2.id, destination_id=airport3.id, distance=1500
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

        payload = {
            "tickets": [
                {"flight": flight1.id, "row": 1, "seat": 1},
                {"flight": flight2.id, "row": 2, "seat": 3},
            ]
        }

        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(id=res.data["id"])
        self.assertEqual(order.tickets.count(), 2)

        ticket_flights = [ticket.flight for ticket in order.tickets.all()]
        self.assertIn(flight1, ticket_flights)
        self.assertIn(flight2, ticket_flights)

    def test_update_order_forbidden(self):
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

        order = sample_order(user=self.user)
        sample_ticket(flight_id=flight.id, order_id=order.id, row=1, seat=1)

        payload = {"tickets": [{"flight": flight.id, "row": 2, "seat": 2}]}

        url = detail_url(order.id)
        res = self.client.put(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_partial_update_order_forbidden(self):
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

        order = sample_order(user=self.user)
        sample_ticket(flight_id=flight.id, order_id=order.id, row=1, seat=1)

        payload = {}

        url = detail_url(order.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_order_forbidden(self):
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

        order = sample_order(user=self.user)
        sample_ticket(flight_id=flight.id, order_id=order.id, row=1, seat=1)

        url = detail_url(order.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cannot_access_other_user_order(self):
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

        other_user = get_user_model().objects.create_user(
            "other@test.com",
            "testpass",
        )

        other_order = sample_order(user=other_user)
        sample_ticket(flight_id=flight.id, order_id=other_order.id, row=1, seat=1)

        url = detail_url(other_order.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
