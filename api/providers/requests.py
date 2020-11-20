from typing import List

from django.db import transaction
from django.db.models import Q
from rest_framework import serializers
from rest_framework.views import APIView

from api.models import User, ProviderRequest, RelatedUserField
from api.notifications import notify_all
from api.serializers import UUIDSerializer
from api.util import MySerializer, jsonify


class CreateProviderRequestSerializer(MySerializer):
    provider_uuid = serializers.UUIDField()


class CreateProviderRequest(APIView):
    """
    To be called by patient to request a provider.
    """
    def post(self, request):
        serializer = CreateProviderRequestSerializer(data=request.data)

        serializer.validate_or_error()

        provider_uuid = serializer.validated_data["provider_uuid"]

        try:
            provider: User = User.objects.get(uuid=provider_uuid)
        except User.DoesNotExist:
            return jsonify(error="User does not exist.", status=400)

        provider_request = ProviderRequest(
            patient=request.user,
            provider=provider
        )

        provider_request.save()

        # Notify the provider that they have a new request
        notify_all(
            provider,
            "New Patient Request", "You have a new patient request. Please check the app to accept or decline it."
        )

        return jsonify(message="success")


class AcceptProviderRequest(APIView):
    """
    To be called by provider to accept request
    """
    def post(self, request):
        serializer = UUIDSerializer(data=request.data)

        serializer.validate_or_error()

        # Find the request
        try:
            provider_request = ProviderRequest.objects.get(uuid = serializer.validated_data["uuid"])
        except ProviderRequest.DoesNotExist:
            return jsonify(error="That request doesn't exist.", status=400)

        # Make sure that the user calling this is the provider
        if provider_request.provider != request.user:
            return jsonify(error="You are not authorized to accept that request.", status=403)

        # We are authorized, assign the new provider
        with transaction.atomic():
            provider_request.patient.provider = provider_request.provider
            provider_request.patient.save()

            provider_request.delete()

            # Delete all the patient's other provider requests
            provider_request.patient.provider_requests_as_patient.all().delete()

        # Notify the patient that their request has been accepted
        notify_all(
            provider_request.patient,
            "Request Accepted",
            "Your provider has accepted you as a patient! You may now go into the app and request your first "
            "appointment."
        )

        return jsonify(message="success")


class DeclineProviderRequest(APIView):
    def post(self, request):
        serializer = UUIDSerializer(data=request.data)

        serializer.validate_or_error()

        # Find the request
        try:
            provider_request = ProviderRequest.objects.get(uuid=serializer.validated_data["uuid"])
        except ProviderRequest.DoesNotExist:
            return jsonify(error="That request doesn't exist.", status=400)

        # Assert that the user is authorized to decline this request (they are either the patient or provider).
        if request.user not in [provider_request.patient, provider_request.provider]:
            return jsonify(error="You are not authorized to decline that request.", status=403)

        provider_request.delete()

        # Notify the patient
        if request.user != provider_request.patient:
            notify_all(
                provider_request.patient,
                "Provider Request Declined",
                "Your provider request has been declined. Please open the app to request someone else."
            )

        return jsonify(message="success")


class ProviderRequestSerializer(serializers.ModelSerializer):
    patient = RelatedUserField(
        read_only=True
    )
    provider = RelatedUserField(
        read_only=True
    )

    class Meta:
        model = ProviderRequest
        fields = ["uuid", "patient", "provider"]


class GetNumPendingProviderRequests(APIView):
    def get(self, request):
        result: int = ProviderRequest.objects.filter(
            Q(patient=request.user) | Q(provider=request.user)
        ).count()

        return jsonify(result=result)


class GetMyProviderRequests(APIView):
    def get(self, request):
        user = request.user

        requests: List[ProviderRequest] = list(ProviderRequest.objects.filter(
            Q(patient=user) | Q(provider=user)
        ).order_by("start_time").all())

        result = [ProviderRequestSerializer(request).data for request in requests]

        return jsonify(result, safe=False)
