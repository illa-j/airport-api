import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport_service.models import (
    Airplane,
    AirplaneType,
)
from airport_service.serializers import AirplaneListSerializer

AIRPLANE_URL = reverse("airport_service:airplane-list")


def detail_url(airplane_id):
    return reverse("airport_service:airplane-detail", args=[airplane_id])


def image_upload_url(airplane_id):
    return reverse("airport_service:airplane-upload-image", args=[airplane_id])


def sample_airplane_type(**params):
    defaults = {"name": "Sample Airplane Type"}
    defaults.update(params)

    return AirplaneType.objects.create(**defaults)


def sample_airplane(**params):
    defaults = {"name": "Sample Airplane", "rows": 30, "seats_in_row": 6}
    defaults.update(params)

    return Airplane.objects.create(**defaults)


class UnauthenticatedAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPLANE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_airplanes(self):
        airplane_type = sample_airplane_type()
        sample_airplane(airplane_type_id=airplane_type.id)
        sample_airplane(name="Sample Airplane 2", airplane_type_id=airplane_type.id)

        res = self.client.get(AIRPLANE_URL)

        airplanes = Airplane.objects.order_by("name")
        serializer = AirplaneListSerializer(airplanes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_airplanes_by_name(self):
        airplane_type = sample_airplane_type()
        airplane1 = sample_airplane(
            name="Airbus A320", airplane_type_id=airplane_type.id
        )
        airplane2 = sample_airplane(
            name="Boeing 737", airplane_type_id=airplane_type.id
        )

        res = self.client.get(AIRPLANE_URL, {"name": "Airbus"})

        serializer1 = AirplaneListSerializer(airplane1)
        serializer2 = AirplaneListSerializer(airplane2)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_filter_airplanes_by_type(self):
        airplane_type1 = sample_airplane_type(name="Passenger")
        airplane_type2 = sample_airplane_type(name="Cargo")

        airplane1 = sample_airplane(
            name="Airbus A320", airplane_type_id=airplane_type1.id
        )
        airplane2 = sample_airplane(
            name="Boeing 747F", airplane_type_id=airplane_type2.id
        )

        res = self.client.get(AIRPLANE_URL, {"type": "Passenger"})

        serializer1 = AirplaneListSerializer(airplane1)
        serializer2 = AirplaneListSerializer(airplane2)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_retrieve_airplane_detail(self):
        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type_id=airplane_type.id)

        url = detail_url(airplane.id)
        res = self.client.get(url)

        serializer = AirplaneListSerializer(airplane)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_airplane_forbidden(self):
        airplane_type = sample_airplane_type()
        payload = {
            "name": "Test Airplane",
            "rows": 30,
            "seats_in_row": 6,
            "airplane_type": airplane_type.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_upload_image_forbidden(self):
        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type_id=airplane_type.id)
        url = image_upload_url(airplane.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_airplane(self):
        airplane_type = sample_airplane_type()
        payload = {
            "name": "Test Airplane",
            "rows": 30,
            "seats_in_row": 6,
            "airplane_type": airplane_type.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        airplane = Airplane.objects.get(id=res.data["id"])

        self.assertEqual(airplane.name, payload["name"])
        self.assertEqual(airplane.rows, payload["rows"])
        self.assertEqual(airplane.seats_in_row, payload["seats_in_row"])
        self.assertEqual(airplane.airplane_type, airplane_type)

    def test_create_airplane_with_invalid_rows_or_seats(self):
        airplane_type = sample_airplane_type()

        payload = {
            "name": "Test Airplane",
            "rows": 0,
            "seats_in_row": 6,
            "airplane_type": airplane_type.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        payload = {
            "name": "Test Airplane",
            "rows": 30,
            "seats_in_row": 0,
            "airplane_type": airplane_type.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_duplicate_airplane_invalid(self):
        airplane_type = sample_airplane_type()
        sample_airplane(name="Airbus A320", airplane_type_id=airplane_type.id)

        payload = {
            "name": "Airbus A320",
            "rows": 35,
            "seats_in_row": 6,
            "airplane_type": airplane_type.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_airplane(self):
        airplane_type = sample_airplane_type()
        airplane = sample_airplane(
            name="Original Airplane",
            rows=30,
            seats_in_row=6,
            airplane_type_id=airplane_type.id,
        )

        payload = {
            "name": "Updated Airplane",
            "rows": 35,
            "seats_in_row": 7,
            "airplane_type": airplane_type.id,
        }

        url = detail_url(airplane.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        airplane.refresh_from_db()
        self.assertEqual(airplane.name, payload["name"])
        self.assertEqual(airplane.rows, payload["rows"])
        self.assertEqual(airplane.seats_in_row, payload["seats_in_row"])

    def test_partial_update_airplane(self):
        airplane_type = sample_airplane_type()
        airplane = sample_airplane(
            name="Original Airplane",
            rows=30,
            seats_in_row=6,
            airplane_type_id=airplane_type.id,
        )

        payload = {"rows": 35}

        url = detail_url(airplane.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        airplane.refresh_from_db()
        self.assertEqual(airplane.rows, payload["rows"])
        self.assertEqual(airplane.name, "Original Airplane")
        self.assertEqual(airplane.seats_in_row, 6)

    def test_upload_image_to_airplane(self):
        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type_id=airplane_type.id)
        url = image_upload_url(airplane.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")

        airplane.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(airplane.image.path))

    def test_upload_image_bad_request(self):
        airplane_type = sample_airplane_type()
        airplane = sample_airplane(airplane_type_id=airplane_type.id)
        url = image_upload_url(airplane.id)

        res = self.client.post(url, {"image": "not an image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_airplane_capacity_property(self):
        airplane_type = sample_airplane_type()
        airplane = sample_airplane(
            rows=30, seats_in_row=6, airplane_type_id=airplane_type.id
        )

        self.assertEqual(airplane.capacity, 180)

    def tearDown(self):
        for airplane in Airplane.objects.all():
            if airplane.image:
                if os.path.exists(airplane.image.path):
                    os.remove(airplane.image.path)
