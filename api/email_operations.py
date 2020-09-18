import logging
import os

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from sendgrid import SendGridAPIClient, Mail

from api.models import User, EmailVerificationToken, PasswordResetToken


def send_verification_email(user: User):
    try:
        token = EmailVerificationToken.objects.get(user=user)
    except EmailVerificationToken.DoesNotExist:
        token = EmailVerificationToken(
            user=user,
            token=os.urandom(44).hex()
        )

        token.save()

    link = f"https://telehelp.giraffemail.org/verify/{token.token}"

    message = Mail(
        from_email='no-reply@telehelp.giraffemail.org',
        to_emails=user.email,
        subject='Verify Telehelp Account',
        html_content=f'Please verify your Telehelp account by clicking <a href="{link}">here</a>. '
                     f'If you cannot click the link then paste this into your browser: {link}.'
    )

    if not settings.RUNNING_DEVSERVER:
        try:
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            sg.send(message)
        except:
            logging.exception("Failed to send verification email.")
    else:
        print("Sent!", token.token)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def send_verification_email_on_signup(sender, instance=None, created=False, **kwargs):
    if created:
        send_verification_email(instance)


def send_password_reset(user: User):
    token = PasswordResetToken(
        user_id=user.id,
        token=os.urandom(44).hex()
    )

    token.save()

    link = f"https://telehelp.giraffemail.org/api/reset-password/{token.token}"

    message = Mail(
        from_email='no-reply@telehelp.giraffemail.org',
        to_emails=user.email,
        subject='Teletherapy Password Reset',
        html_content=f"We received a request to reset the password for your teletherapy account. "
                     f"If this was you, then you may reset your password by clicking this link: "
                     f'<a href="{link}">{link}</a>. Otherwise, you can safely ignore this email.'
    )

    if not settings.RUNNING_DEVSERVER:
        try:
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            sg.send(message)
        except:
            logging.exception("Failed to send password reset email.")
    else:
        print("Sent!", token.token)
