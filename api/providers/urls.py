from django.urls import path

from api import providers
from api.providers import requests

urlpatterns = [
    path("listproviders", providers.ListProviders.as_view()),
    path("getprovider/<str:pid>", providers.GetProviderInformation.as_view()),

    path("getassignedprovider/", providers.GetAssignedProvider.as_view()),
    # path("assignprovider", providers.AssignProvider.as_view()),

    # Requests
    path("num-provider-requests/", requests.GetNumPendingProviderRequests.as_view()),
    path("get-my-requests/", requests.GetMyProviderRequests.as_view()),
    path("create-request/", requests.CreateProviderRequest.as_view()),
    path("accept-request/<str:request_uuid>", requests.AcceptProviderRequest.as_view()),
    path("decline-request/<str:request_uuid>", requests.DeclineProviderRequest.as_view())
]