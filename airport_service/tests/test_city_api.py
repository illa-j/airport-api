from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport_service.models import City
from airport_service.serializers import CityListSerializer
from airport_service.tests.test_country_api import sample_country

CITY_URL = reverse("airport_service:city-list")


def detail_url(city_id):
    return reverse("airport_service:city-detail", args=[city_id])


def sample_city(**params):
    defaults = {"name": "Sample city"}
    defaults.update(params)

    return City.objects.create(**defaults)


class UnauthenticatedCityApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(CITY_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedCityApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_cities(self):
        country = sample_country()
        sample_city(country_id=country.id)
        sample_city(name="Sample city2", country_id=country.id)

        res = self.client.get(CITY_URL)

        cities = City.objects.order_by("id")
        serializer = CityListSerializer(cities, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_cities_by_name(self):
        country = sample_country()
        city = sample_city(name="London", country_id=country.id)
        city2 = sample_city(name="Berlin", country_id=country.id)

        res = self.client.get(CITY_URL, {"name": "London"})

        serializer = CityListSerializer(city)
        serializer2 = CityListSerializer(city2)

        self.assertIn(serializer.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_filter_cities_by_country(self):
        country1 = sample_country(name="United Kingdom")
        country2 = sample_country(name="Germany")
        city = sample_city(name="London", country_id=country1.id)
        city2 = sample_city(name="Berlin", country_id=country2.id)

        res = self.client.get(CITY_URL, {"country": "Germany"})

        serializer = CityListSerializer(city)
        serializer2 = CityListSerializer(city2)

        self.assertNotIn(serializer.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])

    def test_retrieve_city_detail(self):
        country = sample_country(name="United Kingdom")
        city = sample_city(name="London", country_id=country.id)

        url = detail_url(city.id)
        res = self.client.get(url)

        serializer = CityListSerializer(city)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_city_forbidden(self):
        country = sample_country()
        payload = {"name": "City", "country": country.id}
        res = self.client.post(CITY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminCityApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_city(self):
        country = sample_country()
        payload = {"name": "City", "country": country.id}
        res = self.client.post(CITY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        city = City.objects.get(id=res.data["id"])
        for key in payload.keys():
            if key != "country":
                self.assertEqual(payload[key], getattr(city, key))
                continue
            self.assertEqual(country, getattr(city, key))

    def test_create_duplicate_city_invalid(self):
        country = sample_country(name="France")
        sample_city(name="Paris", country_id=country.id)
        payload = {"name": "Paris", "country": country.id}
        res = self.client.post(CITY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_city(self):
        country = sample_country(name="France")
        country2 = sample_country(name="United Kingdom")
        city = sample_city(name="Paris", country_id=country.id)
        payload = {"name": "London", "country": country2.id}

        url = detail_url(city.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        city.refresh_from_db()
        for key in payload.keys():
            if key != "country":
                self.assertEqual(payload[key], getattr(city, key))
                continue
            self.assertEqual(country2, getattr(city, key))

    def test_partial_update_city(self):
        country = sample_country(name="France")
        city = sample_city(name="Paris", country_id=country.id)
        payload = {"name": "Nice", "country": country.id}

        url = detail_url(city.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        city.refresh_from_db()
        self.assertEqual(city.name, payload["name"])

    def test_delete_city(self):
        country = sample_country(name="France")
        city = sample_city(name="Paris", country_id=country.id)

        url = detail_url(city.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(City.objects.filter(id=city.id).exists())
