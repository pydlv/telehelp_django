from django.contrib import admin

# Register your models here.
from api.models import User, AvailabilitySchedule, Appointment


class UserAdmin(admin.ModelAdmin):
    pass


class AvailabilityScheduleAdmin(admin.ModelAdmin):
    pass


class AppointmentAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)
admin.site.register(AvailabilitySchedule, AvailabilityScheduleAdmin)
admin.site.register(Appointment, AppointmentAdmin)
