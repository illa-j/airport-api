from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport_service.models import AirplaneType
from airport_service.serializers import AirplaneTypeSerializer

AIRPLANE_TYPE_URL = reverse("airport_service:airplanetype-list")


def detail_url(airplane_type_id):
    return reverse("airport_service:airplanetype-detail", args=[airplane_type_id])


def sample_airplane_type(**params):
    defaults = {"name": "Sample Airplane Type"}
    defaults.update(params)

    return AirplaneType.objects.create(**defaults)


class UnauthenticatedAirplaneTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPLANE_TYPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_airplane_types(self):
        sample_airplane_type()
        sample_airplane_type(name="Passenger")

        res = self.client.get(AIRPLANE_TYPE_URL)

        airplane_types = AirplaneType.objects.order_by("id")
        serializer = AirplaneTypeSerializer(airplane_types, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_airplane_types_by_name(self):
        airplane_type1 = sample_airplane_type(name="Passenger")
        airplane_type2 = sample_airplane_type(name="Cargo")

        res = self.client.get(AIRPLANE_TYPE_URL, {"name": "Passenger"})

        serializer1 = AirplaneTypeSerializer(airplane_type1)
        serializer2 = AirplaneTypeSerializer(airplane_type2)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_retrieve_airplane_type_detail(self):
        airplane_type = sample_airplane_type()

        url = detail_url(airplane_type.id)
        res = self.client.get(url)

        serializer = AirplaneTypeSerializer(airplane_type)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_airplane_type_forbidden(self):
        payload = {"name": "Test Type"}
        res = self.client.post(AIRPLANE_TYPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirplaneTypeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_airplane_type(self):
        payload = {"name": "Test Type"}
        res = self.client.post(AIRPLANE_TYPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        airplane_type = AirplaneType.objects.get(id=res.data["id"])
        self.assertEqual(payload["name"], airplane_type.name)

    def test_create_duplicate_airplane_type_invalid(self):
        sample_airplane_type(name="Passenger")

        payload = {"name": "Passenger"}
        res = self.client.post(AIRPLANE_TYPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_airplane_type(self):
        airplane_type = sample_airplane_type()

        payload = {"name": "Updated Type"}

        url = detail_url(airplane_type.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        airplane_type.refresh_from_db()
        self.assertEqual(airplane_type.name, payload["name"])

    def test_partial_update_airplane_type(self):
        airplane_type = sample_airplane_type(name="Original Type")

        payload = {"name": "Partially Updated Type"}

        url = detail_url(airplane_type.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        airplane_type.refresh_from_db()
        self.assertEqual(airplane_type.name, payload["name"])

    def test_delete_airplane_type(self):
        airplane_type = sample_airplane_type()

        url = detail_url(airplane_type.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AirplaneType.objects.filter(id=airplane_type.id).exists())
