import os
import secrets

import boto3
from django.conf import settings


class Folders:
    PROFILE_PICTURES = "profile-pictures"


bucket_name = settings.BUCKET_NAME

session = boto3.session.Session()
client = session.client(
    's3',
    region_name=settings.REGION_NAME,
    endpoint_url=settings.ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)


def upload_file(path_to_file: str, folder: str) -> str:
    """
    Uploads a file to s3.
    :param path_to_file: Path to the file to upload.
    :param folder: The folder on S3 to upload the file to. Defined in Folder class.
    :return: the object's ID in S3
    """
    new_id = secrets.token_hex(16)

    _, file_extension = os.path.splitext(path_to_file)

    if file_extension in (".jpg", ".jpeg",):
        content_type = "image/jpeg"
    elif file_extension == ".png":
        content_type = "image/png"
    else:
        raise ValueError("Invalid image format.")

    filename_on_s3 = folder + "/" + new_id

    client.upload_file(path_to_file,
                       bucket_name,
                       filename_on_s3,
                       ExtraArgs={
                           "ACL": "public-read",
                           "ContentType": content_type
                       })

    return new_id
