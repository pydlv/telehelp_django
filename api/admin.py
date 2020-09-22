from django.contrib import admin

# Register your models here.
from api.models import User, AvailabilitySchedule, Appointment, AppointmentRequest


class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "first_name", "last_name", "account_type"]


class AvailabilityScheduleAdmin(admin.ModelAdmin):
    list_display = ["id", "user"]


class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "provider", "start_time", "end_time", "canceled", "explicitly_ended"]


class AppointmentRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "provider", "start_time", "end_time"]


admin.site.register(User, UserAdmin)
admin.site.register(AvailabilitySchedule, AvailabilityScheduleAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(AppointmentRequest, AppointmentRequestAdmin)
