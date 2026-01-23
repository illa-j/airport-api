from django.contrib import admin

from airport_service.models import (
    Airport,
    City,
    Country,
    Route,
    Airplane,
    AirplaneType,
    Crew, Flight,
)

admin.site.register(Airport)
admin.site.register(City)
admin.site.register(Country)
admin.site.register(Route)
admin.site.register(Airplane)
admin.site.register(AirplaneType)
admin.site.register(Crew)
admin.site.register(Flight)
