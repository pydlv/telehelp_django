from typing import List, Optional

from rest_framework.views import APIView

from api import serializers
from api.enums import DayOfWeek
from api.models import AvailabilitySchedule, User
from api.util import jsonify, utcnow

SCHEDULE_SORT_ORDER = [
        DayOfWeek.monday,
        DayOfWeek.tuesday,
        DayOfWeek.wednesday,
        DayOfWeek.thursday,
        DayOfWeek.friday,
        DayOfWeek.saturday,
        DayOfWeek.sunday
    ]


def get_ranking(v):
    for i, item in enumerate(SCHEDULE_SORT_ORDER):
        if item & v:
            return i


class GetAvailabilitySchedules(APIView):
    def get(self, request, provider_uuid=None):
        if provider_uuid is None and request.user.account_type == "p":
            provider = request.user
        elif provider_uuid:
            try:
                provider: User = User.objects.get(uuid=provider_uuid)
            except User.DoesNotExist:
                return jsonify(error="That provider does not exist.", status=400)
        else:
            return jsonify("Please provide a provider.")

        schedules: List[AvailabilitySchedule] = list(AvailabilitySchedule.objects.filter(user=provider).all())

        schedules.sort(key=lambda schedule: get_ranking(schedule.days_of_week))

        result = [{
            "uuid": schedule.uuid,
            "start_date": schedule.start_date.isoformat(),
            "end_date": schedule.end_date.isoformat() if schedule.end_date else None,
            "start_time": schedule.start_time.isoformat("minutes"),
            "end_time": schedule.end_time.isoformat("minutes"),
            "days_of_week": schedule.days_of_week
        } for schedule in schedules]

        return jsonify(result=result)


def check_schedules_overlap(s1: AvailabilitySchedule, s2: AvailabilitySchedule) -> bool:
    if (s2.end_date is None or s1.start_date < s2.end_date) and (s1.end_date is None or s2.start_date < s1.end_date):
        # The two schedules have overlapping dates.
        if s1.days_of_week & s2.days_of_week:
            # They share at least some days of the week
            if s1.start_time < s2.end_time and s2.start_time < s1.end_time:
                # There is overlap
                return True

    return False


class CreateAvailabilitySchedule(APIView):
    def post(self, request):
        serializer = serializers.CreateAvailabilityScheduleSerializer(data=request.data)

        serializer.validate_or_error()

        if request.user.account_type != "p":
            return jsonify(error="You must be a provider to do this.", status=400)

        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]
        start_time = serializer.validated_data["start_time"]
        end_time = serializer.validated_data["end_time"]
        days_of_week = serializer.validated_data["days_of_week"]

        if start_date is None:
            start_date = utcnow().date()

        new_schedule = AvailabilitySchedule(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            days_of_week=days_of_week
        )

        previous_schedules: List[AvailabilitySchedule] = list(request.user.availabilityschedule_set.all())

        for already_existing_schedule in previous_schedules:
            if check_schedules_overlap(already_existing_schedule, new_schedule):
                return jsonify(
                    error="The schedule you are trying to create "
                          "would overlap with a previously existing schedule.",
                    status=400
                )

        new_schedule.save()

        return jsonify(message="success")


class DeleteAvailabilitySchedule(APIView):
    def post(self, request):
        serializer = serializers.DeleteAvailabilityScheduleSerializer(data=request.data)

        serializer.validate_or_error()

        uuid = serializer.validated_data["uuid"]

        schedule: Optional[AvailabilitySchedule] = request.user.availabilityschedule_set.filter(uuid=uuid).first()

        if schedule is None:
            return jsonify(error="That schedule does not exist.", status=400)

        schedule.delete()

        return jsonify(message="success")
