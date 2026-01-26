from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport_service.models import (
    Airport,
    City,
    Country,
)
from airport_service.serializers import AirportListSerializer

AIRPORT_URL = reverse("airport_service:airport-list")


def detail_url(airport_id):
    return reverse("airport_service:airport-detail", args=[airport_id])


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


class UnauthenticatedAirportApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPORT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirportApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_airports(self):
        country = sample_country()
        city = sample_city(country_id=country.id)
        sample_airport(city_id=city.id)
        sample_airport(name="Sample Airport 2", code="SA2", city_id=city.id)

        res = self.client.get(AIRPORT_URL)

        airports = Airport.objects.order_by("id")
        serializer = AirportListSerializer(airports, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_airports_by_name(self):
        country = sample_country()
        city = sample_city(country_id=country.id)
        airport = sample_airport(name="Heathrow Airport", code="LHR", city_id=city.id)
        airport2 = sample_airport(name="Gatwick Airport", code="LGW", city_id=city.id)

        res = self.client.get(AIRPORT_URL, {"name": "Heathrow"})

        serializer = AirportListSerializer(airport)
        serializer2 = AirportListSerializer(airport2)

        self.assertIn(serializer.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_filter_airports_by_city(self):
        country = sample_country()
        city = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Berlin", country_id=country.id)
        airport = sample_airport(name="Heathrow Airport", code="LHR", city_id=city.id)
        airport2 = sample_airport(
            name="Berlin Brandenburg Airport", code="BER", city_id=city2.id
        )

        res = self.client.get(AIRPORT_URL, {"city": "Berlin"})

        serializer = AirportListSerializer(airport)
        serializer2 = AirportListSerializer(airport2)

        self.assertNotIn(serializer.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])

    def test_filter_airports_by_code(self):
        country = sample_country()
        city = sample_city(country_id=country.id)
        airport = sample_airport(name="Heathrow Airport", code="LHR", city_id=city.id)
        airport2 = sample_airport(name="Gatwick Airport", code="LGW", city_id=city.id)

        res = self.client.get(AIRPORT_URL, {"code": "LHR"})

        serializer = AirportListSerializer(airport)
        serializer2 = AirportListSerializer(airport2)

        self.assertIn(serializer.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_create_airport_forbidden(self):
        country = sample_country()
        city = sample_city(country_id=country.id)
        payload = {"name": "Test Airport", "city": city.id, "code": "TST"}
        res = self.client.post(AIRPORT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirportApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_airport(self):
        country = sample_country()
        city = sample_city(country_id=country.id)
        payload = {"name": "Test Airport", "city": city.id, "code": "TST"}
        res = self.client.post(AIRPORT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        airport = Airport.objects.get(id=res.data["id"])
        for key in payload.keys():
            if key != "city":
                self.assertEqual(payload[key], getattr(airport, key))
                continue
            self.assertEqual(city, getattr(airport, key))

    def test_create_duplicate_airport_code_invalid(self):
        country = sample_country()
        city = sample_city(country_id=country.id)
        sample_airport(name="Existing Airport", code="TST", city_id=city.id)

        payload = {"name": "New Airport", "city": city.id, "code": "TST"}
        res = self.client.post(AIRPORT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_airport(self):
        country = sample_country()
        city = sample_city(country_id=country.id)
        airport = sample_airport(name="Original Airport", code="ORI", city_id=city.id)

        payload = {"name": "Updated Airport", "city": city.id, "code": "UPD"}

        url = detail_url(airport.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        airport.refresh_from_db()
        self.assertEqual(airport.name, payload["name"])
        self.assertEqual(airport.code, payload["code"])
        self.assertEqual(airport.city, city)

    def test_partial_update_airport(self):
        country = sample_country()
        city = sample_city(country_id=country.id)
        airport = sample_airport(name="Original Airport", code="ORI", city_id=city.id)

        payload = {"name": "Partially Updated Airport"}

        url = detail_url(airport.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        airport.refresh_from_db()
        self.assertEqual(airport.name, payload["name"])
        self.assertEqual(airport.code, "ORI")

    def test_delete_airport(self):
        country = sample_country()
        city = sample_city(country_id=country.id)
        airport = sample_airport(name="Airport to Delete", code="DEL", city_id=city.id)

        url = detail_url(airport.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Airport.objects.filter(id=airport.id).exists())
