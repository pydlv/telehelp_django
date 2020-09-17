from datetime import datetime

import pytz
from django.http import JsonResponse
from rest_framework import status, serializers
from rest_framework.exceptions import ValidationError


class MySerializer(serializers.Serializer):
    def validate_or_error(self):
        if self.is_valid():
            pass
        else:
            raise ValidationError(self.errors)


def jsonify_old(value, *args, **kwargs):
    if type(value) is str:
        return JsonResponse({"message": value})
    else:
        return JsonResponse(value, *args, **kwargs)


def jsonify(*args, status=status.HTTP_200_OK, **kwargs):
    if args and kwargs:
        raise ValueError("Jsonify does not support both args and kwargs.")

    if len(args) == 1:
        return JsonResponse(*args, status=status)
    elif args:
        return JsonResponse(list(*args), status=status)
    else:
        return JsonResponse(dict(kwargs), status=status)


def bad_request(*args, **kwargs):
    return jsonify_old(*args, status=status.HTTP_400_BAD_REQUEST, **kwargs)


def utcnow():
    return datetime.utcnow().replace(tzinfo=pytz.UTC)
