from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers

from airport_service.models import (
    Country,
    Airport,
    City,
    Route,
    AirplaneType,
    Airplane,
    Crew,
    Flight,
    Order,
    Ticket,
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
        fields = ("id", "name", "city", "code")


class AirportListSerializer(serializers.ModelSerializer):
    city = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="name",
    )
    country = serializers.CharField(source="city.country", read_only=True)

    class Meta:
        model = Airport
        fields = ("id", "name", "city", "country", "code")
        read_only_fields = ("id", "country", "city")


class RouteSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        source = attrs.get("source", self.instance.source if self.instance else None)
        destination = attrs.get(
            "destination", self.instance.destination if self.instance else None
        )

        source_code = source.code if source else None
        destination_code = destination.code if destination else None

        if source_code is not None and destination_code is not None:
            Route.validate_routes(source_code, destination_code, ValidationError)

        return attrs

    class Meta:
        model = Route
        fields = (
            "id",
            "source",
            "destination",
            "distance",
        )


class RouteListSerializer(serializers.ModelSerializer):
    source = serializers.SlugRelatedField(slug_field="name", many=False, read_only=True)
    source_city = serializers.CharField(
        source="source.city.name",
        read_only=True,
    )
    destination = serializers.SlugRelatedField(
        slug_field="name", many=False, read_only=True
    )
    destination_city = serializers.CharField(
        source="destination.city.name",
        read_only=True,
    )

    class Meta:
        model = Route
        fields = (
            "id",
            "source",
            "source_city",
            "destination",
            "destination_city",
            "distance",
        )


class RouteDetailSerializer(serializers.ModelSerializer):
    source = AirportListSerializer(many=False, read_only=True)
    destination = AirportListSerializer(many=False, read_only=True)

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")
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
    def validate(self, attrs):
        Airplane.validate_seats_rows(
            attrs.get("rows", None), attrs.get("seats_in_row", None), ValidationError
        )

        return attrs

    class Meta:
        model = Airplane
        fields = ("id", "name", "rows", "seats_in_row", "airplane_type")


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
            "image",
        )


class AirplaneImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ("id", "image")


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name")


class CrewListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "full_name")


class FlightSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        departure_time = attrs.get(
            "departure_time", self.instance.departure_time if self.instance else None
        )
        arrival_time = attrs.get(
            "arrival_time", self.instance.arrival_time if self.instance else None
        )

        if departure_time is not None and arrival_time is not None:
            Flight.validate_times(departure_time, arrival_time, ValidationError)

        return attrs

    class Meta:
        model = Flight
        fields = ("id", "route", "airplane", "departure_time", "arrival_time")


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
    airplane_image = serializers.ImageField(
        source="airplane.image",
        read_only=True,
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = (
            "id",
            "route_from",
            "route_to",
            "airplane",
            "departure_time",
            "arrival_time",
            "airplane_image",
            "tickets_available",
        )


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["row"], attrs["seat"], attrs["flight"].airplane, ValidationError
        )
        return data

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(many=False, read_only=True)


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class FlightDetailSerializer(FlightSerializer):
    route = RouteDetailSerializer(many=False, read_only=True)
    airplane = AirplaneListSerializer(many=False, read_only=True)
    taken_places = TicketSeatsSerializer(source="tickets", many=True, read_only=True)

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "taken_places",
        )


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
