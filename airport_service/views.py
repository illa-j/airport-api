from django.utils.dateparse import parse_date
from django.db.models import F, Count, Prefetch
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from airport_service.permissions import IsAdminOrIfAuthenticatedReadOnly
from airport_service.models import (
    Country,
    City,
    Airport,
    Route,
    Airplane,
    AirplaneType,
    Crew,
    Flight,
    Order,
    Ticket,
)
from airport_service.serializers import (
    CountrySerializer,
    CitySerializer,
    AirportSerializer,
    AirportListSerializer,
    CityListSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouteDetailSerializer,
    AirplaneListSerializer,
    AirplaneSerializer,
    AirplaneTypeSerializer,
    CrewSerializer,
    CrewListSerializer,
    FlightSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    AirplaneImageSerializer,
    OrderSerializer,
    OrderListSerializer,
)


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        name = self.request.query_params.get("name")

        queryset = self.queryset

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type=OpenApiTypes.STR,
                description="Filter by country name (ex. ?movie=Ukraine)",
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.prefetch_related("country")
    serializer_class = CitySerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return CityListSerializer
        return CitySerializer

    def get_queryset(self):
        name = self.request.query_params.get("name")
        country = self.request.query_params.get("country")

        queryset = self.queryset

        if name:
            queryset = queryset.filter(name__icontains=name)
        if country:
            queryset = queryset.filter(country__name__icontains=country)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type=OpenApiTypes.STR,
                description="Filter by city name (ex. ?name=London)",
            ),
            OpenApiParameter(
                "country",
                type=OpenApiTypes.STR,
                description=("Filter by country name (ex. ?country=United Kingdom)"),
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.select_related("city__country")
    serializer_class = AirportSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return AirportListSerializer
        return AirportSerializer

    def get_queryset(self):
        name = self.request.query_params.get("name")
        city = self.request.query_params.get("city")
        code = self.request.query_params.get("code")

        queryset = self.queryset

        if name:
            queryset = queryset.filter(name__icontains=name)
        if city:
            queryset = queryset.filter(city__name__icontains=city)
        if code:
            queryset = queryset.filter(code__icontains=code)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type=OpenApiTypes.STR,
                description="Filter by airport name (ex. ?name=Heathrow Airport)",
            ),
            OpenApiParameter(
                "city",
                type=OpenApiTypes.STR,
                description=("Filter by city name (ex. ?country=London)"),
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.select_related("source__city", "destination__city")
    serializer_class = RouteSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        elif self.action == "retrieve":
            return RouteDetailSerializer
        return RouteSerializer

    def get_queryset(self):
        source_city = self.request.query_params.get("source_city")
        destination_city = self.request.query_params.get("destination_city")
        distance = self.request.query_params.get("distance")

        queryset = self.queryset

        if source_city:
            queryset = queryset.filter(source__city__name__icontains=source_city)
        if destination_city:
            queryset = queryset.filter(
                destination__city__name__icontains=destination_city
            )
        if distance:
            queryset = queryset.filter(distance=distance)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "source_city",
                type=OpenApiTypes.STR,
                description="Filter by source city name (ex. ?source_city=London)",
            ),
            OpenApiParameter(
                "destination_city",
                type=OpenApiTypes.STR,
                description=(
                    "Filter by destination city name (ex. ?destination_city=London)"
                ),
            ),
            OpenApiParameter(
                "distance",
                type=OpenApiTypes.INT,
                description=("Filter by distance (ex. ?distance=543)"),
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.select_related("airplane_type")
    serializer_class = AirplaneSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return AirplaneListSerializer
        elif self.action == "upload_image":
            return AirplaneImageSerializer
        return AirplaneSerializer

    def get_queryset(self):
        name = self.request.query_params.get("name")
        airplane_type = self.request.query_params.get("type")

        queryset = self.queryset

        if name:
            queryset = queryset.filter(name__icontains=name)
        if airplane_type:
            queryset = queryset.filter(airplane_type__name__icontains=airplane_type)

        return queryset

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        airplane = self.get_object()
        serializer = self.get_serializer(airplane, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type=OpenApiTypes.STR,
                description="Filter by airplane name (ex. ?source_city=Airbus A320)",
            ),
            OpenApiParameter(
                "type",
                type=OpenApiTypes.STR,
                description=("Filter by airplane type (ex. ?type=Passenger)"),
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        name = self.request.query_params.get("name")

        queryset = self.queryset

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type=OpenApiTypes.STR,
                description="Filter by name (ex. ?name=Passenger)",
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return CrewListSerializer
        return CrewSerializer

    def get_queryset(self):
        first_name = self.request.query_params.get("first_name")
        last_name = self.request.query_params.get("last_name")

        queryset = self.queryset

        if first_name:
            queryset = queryset.filter(first_name__icontains=first_name)
        if last_name:
            queryset = queryset.filter(last_name__icontains=last_name)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "first_name",
                type=OpenApiTypes.STR,
                description="Filter by first name (ex. ?first_name=Roger)",
            ),
            OpenApiParameter(
                "last_name",
                type=OpenApiTypes.STR,
                description="Filter by last name (ex. ?last_name=Lum)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class FlightViewSet(viewsets.ModelViewSet):
    queryset = (
        Flight.objects.all()
        .select_related("route__source__city", "route__destination__city", "airplane")
        .annotate(
            tickets_available=(
                F("airplane__rows") * F("airplane__seats_in_row") - Count("tickets")
            )
        )
    )
    serializer_class = FlightSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        elif self.action == "retrieve":
            return FlightDetailSerializer
        return FlightSerializer

    def get_queryset(self):
        route_from = self.request.query_params.get("route_from")
        route_to = self.request.query_params.get("route_to")
        departure = self.request.query_params.get("departure")
        arrival = self.request.query_params.get("arrival")

        queryset = self.queryset

        if route_from:
            queryset = queryset.filter(route__source__city__name__icontains=route_from)
        if route_to:
            queryset = queryset.filter(
                route__destination__city__name__icontains=route_to
            )
        if departure:
            date = parse_date(departure)
            queryset = queryset.filter(departure_time__date=date)
        if arrival:
            date = parse_date(arrival)
            queryset = queryset.filter(arrival_time__date=date)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "route_from",
                type=OpenApiTypes.STR,
                description="Filter by source city name (ex. ?route_from=London)",
            ),
            OpenApiParameter(
                "route_to",
                type=OpenApiTypes.STR,
                description="Filter by destination city name (ex. ?route_to=Berlin)",
            ),
            OpenApiParameter(
                "departure",
                type=OpenApiTypes.STR,
                description="Filter by departure date (ex. ?departure=2026-01-25)",
            ),
            OpenApiParameter(
                "arrival",
                type=OpenApiTypes.STR,
                description="Filter by arrival date (ex. ?arrival=2026-01-26)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Order.objects.prefetch_related(
        Prefetch(
            "tickets",
            queryset=Ticket.objects.select_related(
                "flight__airplane",
                "flight__route__source__city",
                "flight__route__destination__city",
            ),
        )
    )
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)
        if self.action in ("list", "retrieve"):
            queryset = queryset.prefetch_related(
                Prefetch(
                    "tickets",
                    queryset=Ticket.objects.select_related(
                        "flight__airplane",
                        "flight__route__source__city",
                        "flight__route__destination__city",
                    ),
                )
            )
        return queryset

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
