from django.urls import path

from api.appointments import requests

urlpatterns = [
    path("num-pending-requests/", requests.GetNumPendingRequests.as_view()),
    path("get-my-requests/", requests.GetMyAppointmentRequests.as_view()),
    path("create-request/", requests.CreateAppointmentRequest.as_view()),
    path("accept-request/<str:request_uuid>", requests.AcceptAppointmentRequest.as_view()),
    path("decline-request/<str:request_uuid>", requests.DeclineAppointmentRequest.as_view())
]