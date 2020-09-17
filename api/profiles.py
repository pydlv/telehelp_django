import functools
import logging
import os
import pathlib
import secrets

from PIL import Image
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import UploadedFile
from django.http import JsonResponse, HttpResponse
from rest_framework import parsers
from rest_framework.views import APIView

from api import serializers, s3
from api.models import User
from api.s3 import Folders
from api.util import jsonify_old, bad_request


class GetProfile(APIView):
    def get(self, request):
        user: User = request.user

        return JsonResponse({
            "first_name": user.first_name,
            "last_name": user.last_name,
            "birth_date": user.birthday.strftime("%m/%d/%Y") if user.birthday else None,
            "bio": user.bio,
            "profile_image_s3": user.profile_image_s3
        })


class EditProfile(APIView):
    def post(self, request):
        serializer = serializers.EditProfileSerializer(data=request.data)

        serializer.validate_or_error()

        user: User = request.user

        user.first_name = serializer.validated_data["first_name"]
        user.last_name = serializer.validated_data["last_name"]
        user.birthday = serializer.validated_data["birthday"]
        user.bio = serializer.validated_data["bio"]

        user.save()

        return jsonify_old({
            "message": "success",
            "first_name": user.first_name,
            "last_name": user.last_name,
            "birth_date": user.birthday,
            "bio": user.bio
        })


def image_transpose_exif(im: Image):
    """
    https://stackoverflow.com/questions/4228530/pil-thumbnail-is-rotating-my-image

    Apply Image.transpose to ensure 0th row of pixels is at the visual
    top of the image, and 0th column is the visual left-hand side.
    Return the original image if unable to determine the orientation.

    As per CIPA DC-008-2012, the orientation field contains an integer,
    1 through 8. Other values are reserved.

    Parameters
    ----------
    im: PIL.Image
       The image to be rotated.
    """

    exif_orientation_tag = 0x0112
    exif_transpose_sequences = [                   # Val  0th row  0th col
        [],                                        #  0    (reserved)
        [],                                        #  1   top      left
        [Image.FLIP_LEFT_RIGHT],                   #  2   top      right
        [Image.ROTATE_180],                        #  3   bottom   right
        [Image.FLIP_TOP_BOTTOM],                   #  4   bottom   left
        [Image.FLIP_LEFT_RIGHT, Image.ROTATE_90],  #  5   left     top
        [Image.ROTATE_270],                        #  6   right    top
        [Image.FLIP_TOP_BOTTOM, Image.ROTATE_90],  #  7   right    bottom
        [Image.ROTATE_90],                         #  8   left     bottom
    ]

    try:
        seq = exif_transpose_sequences[im._getexif()[exif_orientation_tag]]
    except Exception:
        return im
    else:
        return functools.reduce(type(im).transpose, seq, im)


class UploadProfilePicture(APIView):
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def put(self, request):
        if "file" not in request.data:
            return bad_request("No file was uploaded")

        # file: UploadedFile = list(request.FILES.values())[0]
        file = request.data["file"]

        temp_file_identifier = secrets.token_hex(16)
        filename = "temp/" + temp_file_identifier
        fullpath = pathlib.Path(filename).resolve()
        try:
            with open(filename, "wb") as temp_file:
                temp_file.write(file.read())
            file.close()

            parent_path = fullpath.parents[0]

            # Crop the image to a lower size
            base_width = 300
            with Image.open(fullpath) as image:
                # Determine the image format from the actual file
                image_format = image.format.lower()
                # Assign new filename and filepath
                new_filename = temp_file_identifier + "." + image_format
                new_filepath = os.path.join(parent_path, new_filename)

                image = image_transpose_exif(image)

                width_percent = (base_width / float(image.size[0]))
                height_size = int(float(image.size[1]) * float(width_percent))
                image = image.resize((base_width, height_size), Image.ANTIALIAS)

                try:
                    image.save(new_filepath)

                    object_name = s3.upload_file(new_filepath, Folders.PROFILE_PICTURES)
                finally:
                    os.remove(new_filepath)

            # Update the user's new profile picture in the database
            user: User = request.user
            user.profile_image_s3 = object_name

            user.save()

            return jsonify_old({"object": object_name})
        finally:
            if fullpath:
                os.remove(fullpath)
                pass
