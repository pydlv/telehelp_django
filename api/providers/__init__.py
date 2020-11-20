from typing import List

from django.http import JsonResponse
from rest_framework.views import APIView

from api import serializers
from api.models import User
from api.util import jsonify_old, jsonify


def get_provider_view(provider: User):
    first_name = provider.first_name if provider.first_name else ""
    last_name = provider.last_name if provider.last_name else ""

    return {
        "uuid": provider.uuid,
        "full_name": first_name + " " + last_name,
        "first_name": first_name,
        "last_name": last_name,
        "bio": provider.bio,
        "profile_image_s3": provider.profile_image_s3
    }


class GetAssignedProvider(APIView):
    def get(self, request):
        user: User = request.user

        provider = user.provider

        if provider is None:
            return JsonResponse({
                "provider": None
            })
        else:
            return JsonResponse({
                "provider": get_provider_view(provider)
            })


class ListProviders(APIView):
    def get(self, request):
        providers: List[User] = User.objects.filter(account_type="p").all()

        views = [get_provider_view(provider) for provider in providers]

        return jsonify_old({"providers": views})


class GetProviderInformation(APIView):
    def get(self, request, pid: str):
        try:
            provider: User = User.objects.get(uuid=pid)
        except User.DoesNotExist:
            return jsonify(error="Provider not found.", status=400)

        return jsonify(get_provider_view(provider))


class AssignProvider(APIView):
    def post(self, request):
        serializer = serializers.AssignProviderSerializer(data=request.data)

        serializer.validate_or_error()

        uuid = serializer.validated_data["uuid"]

        try:
            provider: User = User.objects.get(uuid=uuid)
        except User.DoesNotExist:
            return jsonify(error="User does not exist.", status=400)

        if provider.account_type != "p":
            return jsonify(error="That user is not a valid provider.", status=400)

        request.user.provider = provider
        request.user.save()

        return jsonify(message="success")
