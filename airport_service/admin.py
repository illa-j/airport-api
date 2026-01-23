from django.contrib import admin

from airport_service.models import (
    Airport,
    City,
    Country,
    Route
)

admin.site.register(Airport)
admin.site.register(City)
admin.site.register(Country)
admin.site.register(Route)
