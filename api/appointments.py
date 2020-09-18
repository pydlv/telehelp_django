from datetime import timedelta, datetime, time, date
from typing import List, Optional, Union

import pytz
from django.db.models import Q
from rest_framework.views import APIView

from api import serializers
from api.consts import APPOINTMENT_BLOCK_TIME
from api.enums import DayOfWeek
from api.models import User, Appointment, AvailabilitySchedule
from api.util import utcnow, jsonify


class GetMyAppointments(APIView):
    def get(self, request):
        user: User = request.user

        appointments: List[Appointment] = list(Appointment.objects.filter(
            (
                    Q(provider=user) |
                    Q(patient=user)
            ) &
            Q(end_time__gt=utcnow() - timedelta(minutes=30)) &
            Q(explicitly_ended=False) &
            Q(canceled=False)
        ).all())

        appointments.sort(key=lambda appointment: appointment.start_time)

        result = [{
            "uuid": appointment.uuid,
            "provider_uuid": appointment.provider.uuid,
            "start_time": appointment.start_time.isoformat(timespec="minutes"),
            "end_time": appointment.end_time.isoformat(timespec="minutes"),
            "explicitly_ended": appointment.explicitly_ended
        } for appointment in appointments]

        return jsonify(result=result)


def isoweekday_to_enum_weekday(isoweekday: int) -> DayOfWeek:
    if isoweekday == 1:
        return DayOfWeek.monday
    elif isoweekday == 2:
        return DayOfWeek.tuesday
    elif isoweekday == 3:
        return DayOfWeek.wednesday
    elif isoweekday == 4:
        return DayOfWeek.thursday
    elif isoweekday == 5:
        return DayOfWeek.friday
    elif isoweekday == 6:
        return DayOfWeek.saturday
    elif isoweekday == 7:
        return DayOfWeek.sunday
    else:
        raise ValueError


def round_up_nearest_half_hour(t: Union[datetime, time]) -> Union[datetime, time]:
    original_was_time = False

    if isinstance(t, time):
        original_was_time = True
        t = datetime.combine(date.today(), t).replace(tzinfo=t.tzinfo)

    if t.minute not in (0, 30) or t.second != 0 or t.microsecond != 0:
        if t.minute < 30:
            t = t.replace(minute=30)
        else:
            new_hour = t.hour + 1
            if new_hour > 23:
                new_hour = 0
            t = t.replace(hour=new_hour, minute=0)

        t = t.replace(second=0, microsecond=0)

    if original_was_time:
        return t.time().replace(tzinfo=t.tzinfo)
    else:
        return t


class GetAvailableAppointments(APIView):
    def post(self, request):
        serializer = serializers.GetAvailableAppointmentsSerializer(data=request.data)

        serializer.validate_or_error()

        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]

        delta = end_date - start_date

        if delta.days <= 0:
            return jsonify(error="Search start date must become before the end date.", status=400)

        if delta.days > 7:
            return jsonify(error="You can only search up to 7 days at once.", status=400)

        user = request.user

        provider: Optional[User] = user.provider

        if provider is None:
            return jsonify(error="You must select a provider first.", status=400)

        appointments: List[Appointment] = Appointment.objects.filter(
            (
                    Q(patient=user) | Q(provider=user) | Q(provider=user.provider)
            ) &
            Q(canceled=False)
        ).order_by("start_time").all()

        schedules = provider.availabilityschedule_set.all()

        # List of time slots available for scheduling an appointment.
        blocks = []

        date_now = utcnow().date()

        initial_search_date = date_now - timedelta(days=1)

        for schedule in schedules:
            current_date = (initial_search_date if start_date < initial_search_date else start_date)
            while current_date <= end_date and (schedule.end_date is None or current_date < schedule.end_date):
                if isoweekday_to_enum_weekday(current_date.isoweekday()) & schedule.days_of_week:
                    current_time = round_up_nearest_half_hour(schedule.start_time.replace(tzinfo=pytz.utc))

                    current_block = datetime.combine(current_date, current_time)

                    while current_block.time() < schedule.end_time or \
                            (schedule.end_time < schedule.start_time <= current_block.time()):
                        # Only show appointments that are in the future
                        if current_block >= utcnow():
                            # Check if block overlaps with an already existing appointment
                            overlaps = False
                            block_end = current_block + timedelta(minutes=APPOINTMENT_BLOCK_TIME)

                            for appointment in appointments:
                                if appointment.start_time < block_end and current_block < appointment.end_time:
                                    overlaps = True

                            if not overlaps:
                                blocks.append(current_block)

                        current_block += timedelta(minutes=APPOINTMENT_BLOCK_TIME)

                while True:
                    # Keep incrementing the days until we find one that is the correct day of the week
                    current_date += timedelta(days=1)

                    if isoweekday_to_enum_weekday(current_date.isoweekday()) & schedule.days_of_week:
                        break

        blocks.sort()

        return jsonify(result=blocks)


class ScheduleAppointment(APIView):
    def post(self, request):
        serializer = serializers.ScheduleAppointmentSerializer(data=request.data)

        serializer.validate_or_error()

        dt = serializer.validated_data["time"]

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
                if appointment_time.minute in (0, 30) and appointment_time.second == 0 and appointment_time.microsecond == 0:
                    # Check that the time is within the schedule's start and end time
                    if schedule.start_time <= appointment_time < schedule.end_time or \
                            schedule.end_time < schedule.start_time <= appointment_time or \
                            appointment_time < schedule.end_time < schedule.start_time:
                        meets_schedule_requirements = True

        if not meets_schedule_requirements:
            return jsonify(error="That does is not a valid appointment time.", status=400)

        # Check if it would overlap with any preexisting appointments
        dt_end = dt + timedelta(minutes=APPOINTMENT_BLOCK_TIME)

        preexisting_appointments: List[Appointment] = list(Appointment.objects.filter(
            (
                Q(patient=user) |
                Q(provider=user) |
                Q(provider=user.provider)
             ) &
            Q(start_time__lt=dt_end) &
            Q(end_time__gt=dt) &
            Q(canceled=False)
        ).order_by("start_time").all())

        overlaps = len(preexisting_appointments) > 0

        if overlaps:
            return jsonify(error="Cannot schedule because the appointment would overlap with another one.", status=400)

        new_appointment = Appointment(
            patient=user,
            provider=provider,
            start_time=dt,
            end_time=dt_end
        )

        new_appointment.save()

        # TODO: Notify provider and patient

        return jsonify(msg="success")


class CancelAppointment(APIView):
    def post(self, request):
        serializer = serializers.CancelAppointmentSerializer(data=request.data)

        serializer.validate_or_error()

        user = request.user

        uuid = serializer.validated_data["uuid"]

        appointment: Optional[Appointment] = Appointment.objects.filter(
            Q(uuid=uuid) &
            (  # Either the patient or provider can cancel the appointment
                Q(patient=user) |
                Q(provider=user)
            )
        ).first()

        if appointment is None:
            return jsonify(error="Appointment does not exist.", status=400)

        start_time = appointment.start_time.replace(tzinfo=pytz.utc)

        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)

        if start_time <= utc_now:
            return jsonify(error="You cannot cancel an appointment that has already started.", status=400)

        appointment.canceled = True
        appointment.save()

        # TODO: Notify both parties

        return jsonify(msg="success")