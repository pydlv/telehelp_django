from typing import Union, List

from django.core.mail import send_mail
from push_notifications.models import GCMDevice, APNSDevice

from api.models import User


def notify_all(users: Union[User, List[User]], title: str, message: str):
    """
    Sends a notification to both the user's email address and push notification depending on their preferences
    :param users: The users to notify
    :param title: The title of the notification
    :param message: The message for the notification
    :return:
    """
    def notify_user(user: User):
        send_mail(
            title,
            message,
            "no-reply@giraffemail.org",
            [user.email]
        )

        send_push(user, message)

    if isinstance(users, list):
        for user in users:
            notify_user(user)
    else:
        notify_user(users)


def send_push(user: User, message: str):
    gmc_devices = GCMDevice.objects.filter(user=user)
    gmc_devices.send_message(message)

    apns_devices = APNSDevice.objects.filter(user=user)
    apns_devices.send_message(message)
