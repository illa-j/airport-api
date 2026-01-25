from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport_service.models import Country
from airport_service.serializers import CountrySerializer

COUNTRY_URL = reverse("airport_service:country-list")


def detail_url(country_id):
    return reverse("airport_service:country-detail", args=[country_id])


def sample_country(**params):
    defaults = {"name": "Sample country"}
    defaults.update(params)

    return Country.objects.create(**defaults)


class UnauthenticatedCountryApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(COUNTRY_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedCountryApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_countries(self):
        sample_country()
        sample_country(name="Sample country2")

        res = self.client.get(COUNTRY_URL)

        countries = Country.objects.order_by("id")
        serializer = CountrySerializer(countries, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_countries_by_name(self):
        country = sample_country(name="France")
        country2 = sample_country(name="Ukraine")

        res = self.client.get(COUNTRY_URL, {"name": "France"})

        serializer = CountrySerializer(country)
        serializer2 = CountrySerializer(country2)

        self.assertIn(serializer.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_retrieve_country_detail(self):
        country = sample_country(name="United Kingdom")

        url = detail_url(country.id)
        res = self.client.get(url)

        serializer = CountrySerializer(country)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_country_forbidden(self):
        payload = {"name": "Country"}
        res = self.client.post(COUNTRY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminCountryApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_country(self):
        payload = {"name": "Country"}
        res = self.client.post(COUNTRY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        country = Country.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(country, key))

    def test_create_duplicate_country_invalid(self):
        sample_country(name="Ukraine")

        payload = {"name": "Ukraine"}
        res = self.client.post(COUNTRY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_country(self):
        country = sample_country(name="Ukraine")

        payload = {"name": "Updated Type"}

        url = detail_url(country.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        country.refresh_from_db()
        self.assertEqual(country.name, payload["name"])

    def test_partial_update_country(self):
        country = sample_country(name="Ukraine")

        payload = {"name": "Partially Updated Type"}

        url = detail_url(country.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        country.refresh_from_db()
        self.assertEqual(country.name, payload["name"])

    def test_delete_airplane_type(self):
        country = sample_country(name="Ukraine")

        url = detail_url(country.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Country.objects.filter(id=country.id).exists())
