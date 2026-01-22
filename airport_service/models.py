from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)

    class Meta:
        unique_together = ("name", "country")

    def __str__(self):
        return f"{self.name} - {self.country}"


class Airport(models.Model):
    name = models.CharField(max_length=100)
    city = models.ForeignKey(City, on_delete=models.PROTECT)

    class Meta:
        unique_together = ("name", "city")

    def __str__(self):
        return f"{self.name} ({self.city})"


class Route(models.Model):
    source = models.ForeignKey(
        Airport,
        on_delete=models.PROTECT,
        related_name="routes_from"
    )
    destination = models.ForeignKey(
        Airport,
        on_delete=models.PROTECT,
        related_name="routes_to"
    )
    distance = models.PositiveIntegerField()

    class Meta:
        unique_together = ("source", "destination")
        indexes = [
            models.Index(fields=["source", "destination"]),
        ]
    def __str__(self):
        return f"{self.source.name} -> {self.destination.name}: {self.distance}km"
