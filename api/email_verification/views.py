from pyexpat import model

from django.http import JsonResponse, HttpResponse
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from api.email_operations import send_verification_email
from api.models import EmailVerificationToken


class GetVerificationStatus(APIView):
    def get(self, request):
        return JsonResponse({
            "result": request.user.verified_email
        })


class SendVerification(APIView):
    def post(self, request):
        send_verification_email(request.user)

        return JsonResponse({
            "message": "success"
        })


class CheckVerification(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, token: str):
        try:
            token = EmailVerificationToken.objects.get(token=token)

            user = token.user
            user.verified_email = True

            user.save()

            token.delete()

            return HttpResponse("You have successfully verified your email!")
        except EmailVerificationToken.DoesNotExist:
            return HttpResponse("That is not a valid token.")
