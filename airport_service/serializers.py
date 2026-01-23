from rest_framework import serializers

from airport_service.models import (
    Country,
    Airport,
    City,
)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = "__all__"


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = "__all__"


class CityListSerializer(serializers.ModelSerializer):
    country = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="name",
    )

    class Meta:
        model = City
        fields = (
            "id",
            "name",
            "country",
        )


class AirportListSerializer(serializers.ModelSerializer):
    city = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="name",
    )
    country = serializers.CharField(
        source="city.country",
        read_only=True
    )

    class Meta:
        model = Airport
        fields = (
            "id",
            "name",
            "city",
            "country",
            "code"
        )
        read_only_fields = (
            "id",
            "country",
            "city"
        )


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = (
            "id",
            "name",
            "city",
            "code"
        )
