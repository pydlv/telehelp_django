from datetime import timedelta, datetime
from typing import Optional

from django.conf import settings
from opentok import opentok, MediaModes, ArchiveModes, Roles
from django.db.models import Q
from rest_framework.views import APIView

from api.models import Appointment
from api.util import jsonify, utcnow


opentok = opentok.OpenTok(settings.TOKBOX_API_KEY, settings.TOKBOX_API_SECRET)


class GetOTToken(APIView):
    def get(self, request, appointment_uuid: str):
        user = request.user

        appointment: Optional[Appointment] = Appointment.objects.filter(
            Q(uuid=appointment_uuid) &
            (
                Q(patient=user) |
                Q(provider=user)
            )
        ).first()

        if appointment is None:
            return jsonify(error="That appointment does not exist.", status=400)

        absolute_latest_end_time = appointment.end_time + timedelta(minutes=5)

        if utcnow() >= absolute_latest_end_time:
            return jsonify(error="That appointment has already ended.", status=400)

        if appointment.ot_session_id is None:
            # We do not already have a session, so we need to get one from OT
            session = opentok.create_session(
                media_mode=MediaModes.relayed,
                archive_mode=ArchiveModes.manual
            )

            session_id = session.session_id

            appointment.ot_session_id = session_id

            appointment.save()
        else:
            session_id = appointment.ot_session_id

        token = opentok.generate_token(
            session_id,
            role=Roles.publisher,
            expire_time=int(datetime.timestamp(absolute_latest_end_time))
        )

        return jsonify(session_id=session_id, token=token)


class EndAppointment(APIView):
    def post(self, request, appointment_uuid: str):
        user = request.user

        appointment: Optional[Appointment] = Appointment.objects.filter(
            Q(uuid=appointment_uuid) &
            (
                    Q(patient=user) |
                    Q(provider=user)
            )
        ).first()

        if appointment is None:
            return jsonify(error="That appointment does not exist.", status=400)

        absolute_latest_end_time = appointment.end_time + timedelta(minutes=10)

        if utcnow() >= absolute_latest_end_time:
            return jsonify(error="That appointment has already ended."), 400

        appointment.explicitly_ended = True

        appointment.save()

        return jsonify(message="success")
