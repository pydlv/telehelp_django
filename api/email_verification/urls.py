from django.conf.urls import url
from django.urls import path

from api.email_verification import views

urlpatterns = [
    url(r"^status/", views.GetVerificationStatus.as_view()),
    url(r"^resend/", views.SendVerification.as_view()),
    path("<str:token>", views.CheckVerification.as_view())
]
