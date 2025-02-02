from django.conf.urls import url
from django.urls import path, include

import api.auth
from api import profiles, providers, schedules, video_sessions, push_notifs
from api.appointments import appointments

urlpatterns = [
    # Auth
    url(r'^api-token-auth/', api.auth.obtain_auth_token),
    url(r'^signup/', api.auth.registration_view),

    path('verify/', include('api.email_verification.urls')),
    path('', include("api.password_change.urls")),

    # Device registration for push notifications
    path("device/", include(push_notifs.router.urls)),

    # Profile
    url(r"^profile/", profiles.GetProfile.as_view()),
    path("editprofile", profiles.EditProfile.as_view()),
    path("upload-profile-picture", profiles.UploadProfilePicture.as_view()),

    # Providers
    path("providers/", include("api.providers.urls")),

    # Schedules
    path("get-availability-schedules", schedules.GetAvailabilitySchedules.as_view()),
    path("get-availability-schedules/<str:provider_uuid>", schedules.GetAvailabilitySchedules.as_view()),

    path("availability-schedules/create", schedules.CreateAvailabilitySchedule.as_view()),
    path("availability-schedules/delete", schedules.DeleteAvailabilitySchedule.as_view()),

    # Appointments
    path("appointments/", include("api.appointments.urls")),
    path("get-my-appointments", appointments.GetMyAppointments.as_view()),
    path("get-available-appointments", appointments.GetAvailableAppointments.as_view()),
    path("cancel-appointment", appointments.CancelAppointment.as_view()),
    path("get-ot-token/<str:appointment_uuid>", video_sessions.GetOTToken.as_view()),
    path("end-appointment/<str:appointment_uuid>", video_sessions.EndAppointment.as_view()),
]
