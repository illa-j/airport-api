from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport_service.models import Crew
from airport_service.serializers import (
    CrewListSerializer,
    CrewSerializer,
)

CREW_URL = reverse("airport_service:crew-list")


def detail_url(crew_id):
    return reverse("airport_service:crew-detail", args=[crew_id])


def sample_crew(**params):
    defaults = {"first_name": "John", "last_name": "Doe"}
    defaults.update(params)

    return Crew.objects.create(**defaults)


class UnauthenticatedCrewApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(CREW_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedCrewApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_crew(self):
        sample_crew()
        sample_crew(first_name="Jane", last_name="Smith")

        res = self.client.get(CREW_URL)

        crew = Crew.objects.order_by("id")
        serializer = CrewListSerializer(crew, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_crew_by_first_name(self):
        crew1 = sample_crew(first_name="Roger", last_name="Lum")
        crew2 = sample_crew(first_name="Jane", last_name="Smith")

        res = self.client.get(CREW_URL, {"first_name": "Roger"})

        serializer1 = CrewListSerializer(crew1)
        serializer2 = CrewListSerializer(crew2)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_filter_crew_by_last_name(self):
        crew1 = sample_crew(first_name="Roger", last_name="Lum")
        crew2 = sample_crew(first_name="Jane", last_name="Smith")

        res = self.client.get(CREW_URL, {"last_name": "Lum"})

        serializer1 = CrewListSerializer(crew1)
        serializer2 = CrewListSerializer(crew2)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])

    def test_filter_crew_by_first_and_last_name(self):
        crew1 = sample_crew(first_name="Roger", last_name="Lum")
        crew2 = sample_crew(first_name="Roger", last_name="Smith")
        crew3 = sample_crew(first_name="Jane", last_name="Lum")

        res = self.client.get(CREW_URL, {"first_name": "Roger", "last_name": "Lum"})

        serializer1 = CrewListSerializer(crew1)
        serializer2 = CrewListSerializer(crew2)
        serializer3 = CrewListSerializer(crew3)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertNotIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_retrieve_crew_detail(self):
        crew = sample_crew()

        url = detail_url(crew.id)
        res = self.client.get(url)

        serializer = CrewListSerializer(crew)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_crew_forbidden(self):
        payload = {"first_name": "Test", "last_name": "User"}
        res = self.client.post(CREW_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminCrewApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_crew(self):
        payload = {"first_name": "Test", "last_name": "User"}
        res = self.client.post(CREW_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        crew = Crew.objects.get(id=res.data["id"])
        self.assertEqual(payload["first_name"], crew.first_name)
        self.assertEqual(payload["last_name"], crew.last_name)

    def test_update_crew(self):
        crew = sample_crew(first_name="Original", last_name="Name")

        payload = {"first_name": "Updated", "last_name": "Name"}

        url = detail_url(crew.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        crew.refresh_from_db()
        self.assertEqual(crew.first_name, payload["first_name"])
        self.assertEqual(crew.last_name, payload["last_name"])

    def test_partial_update_crew(self):
        crew = sample_crew(first_name="Original", last_name="Name")

        payload = {"first_name": "Partially Updated"}

        url = detail_url(crew.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        crew.refresh_from_db()
        self.assertEqual(crew.first_name, payload["first_name"])
        self.assertEqual(crew.last_name, "Name")

    def test_delete_crew(self):
        crew = sample_crew()

        url = detail_url(crew.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Crew.objects.filter(id=crew.id).exists())

    def test_crew_full_name_property(self):
        crew = sample_crew(first_name="Roger", last_name="Lum")

        self.assertEqual(crew.full_name, "Roger Lum")
