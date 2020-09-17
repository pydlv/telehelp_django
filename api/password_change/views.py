from django.http import HttpResponse
from django.template import loader
from rest_framework import permissions, status, parsers
from rest_framework.views import APIView

from api.email_operations import send_password_reset
from api.models import User, PasswordResetToken
from api.password_change import serializers
from api.password_change.serializers import PasswordChangeSerializer
from api.util import bad_request, jsonify_old, utcnow


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)

        if serializer.is_valid():
            user: User = request.user

            password_correct = user.check_password(serializer.validated_data["old_password"])

            if password_correct:
                user.set_password(serializer.validated_data["new_password"])
                user.save()
                return HttpResponse("Successfully updated password.")
            else:
                return bad_request("Invalid password")
        else:
            return bad_request(serializer.errors)


class RequestPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = serializers.RequestPasswordResetSerializer(data=request.data)

        serializer.validate_or_error()

        email: str = serializer.validated_data["email"].lower()

        try:
            user: User = User.objects.get(email=email)
        except User.DoesNotExist:
            return bad_request("User does not exist.")

        send_password_reset(user)

        return jsonify_old("Request successful. Please check your email for a password reset link.")


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [parsers.FormParser]

    def get(self, request, token):
        template = loader.get_template("password-change/password-reset.html")

        context = {
            "token": token
        }

        return HttpResponse(template.render(context, request))

    def post(self, request, token):
        serializer = serializers.ResetPasswordFormSerializer(data=request.data)
        serializer.validate_or_error()

        try:
            token = PasswordResetToken.objects.get(token=serializer.validated_data["token"])
        except PasswordResetToken.DoesNotExist:
            return HttpResponse("That password reset token is invalid.", status=status.HTTP_400_BAD_REQUEST)

        if token.expires is not None and token.expires <= utcnow():
            return HttpResponse("That password reset token has expired.", status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        user = token.user

        if user.email.lower() != email.lower():
            return HttpResponse("The email you entered is not correct.")

        token.delete()

        # Everything checks out, go ahead and reset the password
        user.set_password(serializer.validated_data["password"])
        user.save()

        return HttpResponse("Password reset successful. You can now log into the app.")
