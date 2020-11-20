import re

from rest_framework import serializers

from api import models
from api.enums import DayOfWeek
from api.models import User
from api.util import MySerializer


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(style={"input_type": "password"}, min_length=6)
    confirm_password = serializers.CharField(style={"input_type": "password"}, write_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "confirm_password"]
        extra_kwargs = {k: {'write_only': True} for k in fields}

    def save(self):
        user = User(
            email=self.validated_data["email"]
        )

        password = self.validated_data["password"]
        password_confirm = self.validated_data["confirm_password"]

        if password != password_confirm:
            raise serializers.ValidationError({"password": "The passwords must match."})

        user.set_password(password)
        user.save()

        return user

    def validate_email(self, value):
        norm_email = value.lower()

        if not re.search(r'\S+@\S+\.\S+', norm_email):
            raise serializers.ValidationError("Invalid email format.")

        if models.User.objects.filter(email=norm_email).exists():
            raise serializers.ValidationError("A user with this email already exists.")

        return norm_email


class EditProfileSerializer(MySerializer):
    first_name = serializers.CharField(min_length=3, max_length=30)
    last_name = serializers.CharField(min_length=3, max_length=30)
    birthday = serializers.DateField(format="MM/DD/YYYY")
    bio = serializers.CharField(allow_null=True)


class UUIDSerializer(MySerializer):
    uuid = serializers.UUIDField()


class AssignProviderSerializer(MySerializer):
    uuid = serializers.UUIDField()


class CreateAvailabilityScheduleSerializer(MySerializer):
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    days_of_week = serializers.IntegerField(min_value=1, max_value=DayOfWeek.all)


class DeleteAvailabilityScheduleSerializer(MySerializer):
    uuid = serializers.UUIDField()


class GetAvailableAppointmentsSerializer(MySerializer):
    start_date = serializers.DateField(format="iso-8601")
    end_date = serializers.DateField(format="iso-8601")


class ScheduleAppointmentSerializer(MySerializer):
    time = serializers.DateTimeField(format="iso-8601")


class CancelAppointmentSerializer(MySerializer):
    uuid = serializers.UUIDField()
