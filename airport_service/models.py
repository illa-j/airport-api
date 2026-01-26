import os
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(
        Country, on_delete=models.PROTECT, related_name="cities"
    )

    class Meta:
        unique_together = ("name", "country")
        verbose_name_plural = "Cities"

    def __str__(self):
        return self.name


class Airport(models.Model):
    name = models.CharField(max_length=100)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name="airports")
    code = models.CharField(
        max_length=4,
        unique=True,
        default="XXX",
        help_text="IATA (3) or ICAO (4) airport code",
    )

    def __str__(self):
        return f"{self.name} - {self.code}"


class Route(models.Model):
    source = models.ForeignKey(
        Airport, on_delete=models.PROTECT, related_name="routes_from"
    )
    destination = models.ForeignKey(
        Airport, on_delete=models.PROTECT, related_name="routes_to"
    )
    distance = models.PositiveIntegerField()

    class Meta:
        unique_together = ("source", "destination")
        indexes = [
            models.Index(fields=["source", "destination"]),
        ]

    def __str__(self):
        return f"Distance {self.distance}km: Airport {self.source_id} to {self.destination_id}"

    @staticmethod
    def validate_routes(source_code, destination_code, error_to_raise):
        if source_code == destination_code:
            raise error_to_raise("Source and destination must be different")

    def clean(self):
        Route.validate_routes(
            self.source.code,
            self.destination.code,
            ValidationError,
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(Route, self).save(*args, **kwargs)


class AirplaneType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


def airplane_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.name)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/airplanes/", filename)


class Airplane(models.Model):
    name = models.CharField(max_length=100)
    rows = models.PositiveIntegerField()
    seats_in_row = models.PositiveIntegerField()
    airplane_type = models.ForeignKey(
        AirplaneType, on_delete=models.PROTECT, related_name="airplanes"
    )
    image = models.ImageField(blank=True, null=True, upload_to=airplane_image_file_path)

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    class Meta:
        unique_together = ("name", "airplane_type")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.rows}:{self.seats_in_row}"

    @staticmethod
    def validate_seats_rows(rows, seats_in_row, error_to_raise):
        if rows is not None and rows < 1:
            raise error_to_raise("Rows must be greater than zero.")
        if seats_in_row is not None and seats_in_row < 1:
            raise error_to_raise("Seats must be greater than zero.")

    def clean(self):
        Airplane.validate_seats_rows(self.rows, self.seats_in_row, ValidationError)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(Airplane, self).save(*args, **kwargs)


class Crew(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Flight(models.Model):
    route = models.ForeignKey(Route, on_delete=models.PROTECT, related_name="flights")
    airplane = models.ForeignKey(
        Airplane, on_delete=models.PROTECT, related_name="flights"
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        ordering = ["-departure_time"]

    def __str__(self):
        return f"{self.route} {self.airplane.name} {self.departure_time}: {self.arrival_time}"

    @staticmethod
    def validate_times(departure_time, arrival_time, error_to_raise):
        if departure_time >= arrival_time:
            raise error_to_raise("Departure time must be before arrival time")

    def clean(self):
        Flight.validate_times(self.departure_time, self.arrival_time, ValidationError)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.PROTECT, related_name="orders"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} by {self.user}"


class Ticket(models.Model):
    flight = models.ForeignKey(Flight, on_delete=models.PROTECT, related_name="tickets")
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="tickets")
    row = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()

    @staticmethod
    def validate_ticket(row, seat, airplane, error_to_raise):
        for ticket_attr_value, ticket_attr_name, airplane_attr_name in [
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ]:
            count_attrs = getattr(airplane, airplane_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                        f"number must be in available range: "
                        f"(1, {airplane_attr_name}): "
                        f"(1, {count_attrs})"
                    }
                )

    def clean(self):
        Ticket.validate_ticket(
            self.row,
            self.seat,
            self.flight.airplane,
            ValidationError,
        )

    def save(
        self,
        *args,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    class Meta:
        unique_together = ("row", "seat", "flight")
        ordering = ["row", "seat"]

    def __str__(self):
        return f"{str(self.flight)} (row: {self.row}, seat: {self.seat})"
