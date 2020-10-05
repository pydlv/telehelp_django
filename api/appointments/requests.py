from datetime import timedelta
from typing import List, Optional

from django.db import transaction
from django.db.models import Q
from rest_framework import serializers
from rest_framework.views import APIView

from api.appointments.appointments import isoweekday_to_enum_weekday
from api.consts import APPOINTMENT_BLOCK_TIME
from api.models import AppointmentRequest, Appointment, User, AvailabilitySchedule
from api.notifications import notify_all
from api.util import jsonify, MySerializer


class RelatedUserField(serializers.RelatedField):
    def to_representation(self, user: Optional[User]):
        if user is None:
            return None

        return {
            "uuid": user.uuid,
            "first_name": user.first_name,
            "last_name": user.last_name
        }


class AppointmentRequestSerializer(serializers.ModelSerializer):
    patient = RelatedUserField(
        read_only=True
    )
    provider = RelatedUserField(
        read_only=True
    )

    class Meta:
        model = AppointmentRequest
        fields = ["uuid", "patient", "provider", "start_time", "end_time"]


class GetNumPendingRequests(APIView):
    def get(self, request):
        result: int = AppointmentRequest.objects.filter(
            Q(patient=request.user) | Q(provider=request.user)
        ).count()

        return jsonify(result=result)


class GetMyAppointmentRequests(APIView):
    def get(self, request):
        user = request.user

        requests: List[AppointmentRequest] = list(AppointmentRequest.objects.filter(
            Q(patient=user) | Q(provider=user)
        ).order_by("start_time").all())

        result = [AppointmentRequestSerializer(request).data for request in requests]

        return jsonify(result, safe=False)


class CreateAppointmentRequestSerializer(MySerializer):
    time = serializers.DateTimeField(format="iso-8601")


class CreateAppointmentRequest(APIView):
    def post(self, request):
        serializer = CreateAppointmentRequestSerializer(data=request.data)

        serializer.validate_or_error()

        dt = serializer.validated_data["time"]
        dt_end = dt + timedelta(minutes=APPOINTMENT_BLOCK_TIME)

        user = request.user

        provider: Optional[User] = user.provider

        if provider is None:
            return jsonify(error="You must select a provider first.", status=400)

        schedules: List[AvailabilitySchedule] = list(provider.availabilityschedule_set.all())

        meets_schedule_requirements = False

        appointment_time = dt.time()

        for schedule in schedules:
            # Check if it is the correct day of week
            if isoweekday_to_enum_weekday(dt.date().isoweekday()) & schedule.days_of_week or \
                    (
                            appointment_time < schedule.end_time < schedule.start_time and  # We wrapped around to next day
                            isoweekday_to_enum_weekday(
                                (dt.date() - timedelta(days=1)).isoweekday()  # Previous day's day of week number
                            ) & schedule.days_of_week  # Check that previous day was the correct day of week
                    ):
                # Check that the time is on one of the half hours
                if appointment_time.minute in (
                0, 30) and appointment_time.second == 0 and appointment_time.microsecond == 0:
                    # Check that the time is within the schedule's start and end time
                    if schedule.start_time <= appointment_time < schedule.end_time or \
                            schedule.end_time < schedule.start_time <= appointment_time or \
                            appointment_time < schedule.end_time < schedule.start_time:
                        meets_schedule_requirements = True

        if not meets_schedule_requirements:
            return jsonify(error="That does is not a valid appointment time.", status=400)


        appointment_request = AppointmentRequest(
            patient=user,
            provider=provider,
            start_time=dt,
            end_time=dt_end
        )

        appointment_request.save()

        notify_all(
            user.provider,
            "New Appointment Request",
            "One of your clients has requested an appointment. Please open the app to confirm it."
        )

        return jsonify(message="success")


class AcceptAppointmentRequest(APIView):
    def post(self, request, request_uuid):
        user = request.user

        try:
            appointment_request: AppointmentRequest = AppointmentRequest.objects.get(
                Q(uuid=request_uuid) &
                (
                    Q(provider=request.user) |
                    Q(patient=request.user)
                )
            )
        except AppointmentRequest.DoesNotExist:
            return jsonify(error="That appointment request does not exist.", status=400)

        if request.user != appointment_request.provider:
            return jsonify(error="You are not authorized to accept that request.", status=400)

        # Check if it would overlap with any preexisting appointments
        preexisting_appointments: List[Appointment] = list(Appointment.objects.filter(
            (
                    Q(patient=user) |
                    Q(provider=user) |
                    Q(provider=appointment_request.provider)
            ) &
            Q(start_time__lt=appointment_request.end_time) &
            Q(end_time__gt=appointment_request.start_time) &
            Q(canceled=False)
        ).order_by("start_time").all())

        overlaps = len(preexisting_appointments) > 0

        if overlaps:
            return jsonify(error="Cannot schedule because the appointment would overlap with an existing one.",
                           status=400)

        with transaction.atomic():
            appointment_request.delete()

            appointment = Appointment(
                patient=appointment_request.patient,
                provider=appointment_request.provider,
                start_time=appointment_request.start_time,
                end_time=appointment_request.end_time,
            )

            appointment.save()

        # Notify the provider
        notify_all(
            appointment_request.provider,
            "Confirmed Appointment",
            "You have accepted a new appointment! Please open the app to view it."
        )

        # Notify the client
        notify_all(
            appointment_request.patient,
            "Confirmed Appointment",
            "You provider has accepted one of your appointment requests. Please open the app to see your "
            "scheduled appointment."
        )

        return jsonify(message="success", uuid=appointment.uuid)


class DeclineAppointmentRequest(APIView):
    def post(self,  request, request_uuid):
        try:
            appointment_request: AppointmentRequest = AppointmentRequest.objects.get(
                Q(uuid=request_uuid) &
                (
                    Q(provider=request.user) |
                    Q(patient=request.user)
                )
            )
        except AppointmentRequest.DoesNotExist:
            return jsonify(error="That appointment request does not exist.", status=400)

        appointment_request.delete()

        if appointment_request.patient != request.user:
            # Notify the client
            notify_all(
                appointment_request.patient,
                "Appointment Request Declined",
                "Your provider has declined your appointment request. Please open the app to request a different time."
            )

        return jsonify(message="success")
