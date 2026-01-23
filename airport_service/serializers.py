from rest_framework import serializers

from airport_service.models import (
    Country,
    Airport,
    City,
    Route,
    AirplaneType,
    Airplane, Crew, Flight,
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


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = (
            "id",
            "name",
            "city",
            "code"
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


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = (
            "id",
            "source",
            "destination",
            "distance",
        )


class RouteListSerializer(serializers.ModelSerializer):
    source_airport_name = serializers.CharField(
        source="source.name",
        read_only=True
    )
    source_airport_city = serializers.CharField(
        source="source.city.name",
        read_only=True,
    )
    destination_airport_name = serializers.CharField(
        source="destination.name",
        read_only=True
    )
    destination_airport_city = serializers.CharField(
        source="destination.city.name",
        read_only=True,
    )

    class Meta:
        model = Route
        fields = (
            "id",
            "source_airport_name",
            "source_airport_city",
            "destination_airport_name",
            "destination_airport_city",
            "distance"
        )


class RouteRetrieveSerializer(serializers.ModelSerializer):
    source = AirportListSerializer(many=False, read_only=True)
    destination = AirportListSerializer(many=False, read_only=True)

    class Meta:
        model = Route
        fields = (
            "id",
            "source",
            "destination",
            "distance"
        )
        read_only_fields = (
            "id",
            "source",
            "destination",
        )


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = "__all__"


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type"
        )


class AirplaneListSerializer(serializers.ModelSerializer):
    airplane_type = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="name",
    )
    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
            "capacity",
            "image"
        )


class AirplaneImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = (
            "id",
            "image"
        )


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = (
            "id",
            "first_name",
            "last_name"
        )


class CrewListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = (
            "id",
            "first_name",
            "last_name",
            "full_name"
        )


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time"
        )


class FlightListSerializer(serializers.ModelSerializer):
    route_from = serializers.CharField(
        source="route.source.city.name",
        read_only=True,
    )
    route_to = serializers.CharField(
        source="route.destination.city.name",
        read_only=True,
    )
    airplane = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="name",
    )

    class Meta:
        model = Flight
        fields = (
            "id",
            "route_from",
            "route_to",
            "airplane",
            "departure_time",
            "arrival_time"
        )



class FlightRetrieveSerializer(FlightSerializer):
    route = RouteRetrieveSerializer(many=False, read_only=True)
    airplane = AirplaneListSerializer(many=False, read_only=True)
