import uuid as uuid
from datetime import datetime, timedelta
from typing import Optional

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from api.consts import SESSION_TOKEN_LENGTH
from api.util import utcnow


def in_three_days():
    return utcnow() + timedelta(days=3)


def current_date():
    return datetime.utcnow().date()


ACCOUNT_TYPE = (
    ('u', 'User'),
    ('p', 'Provider')
)


class VersionedEntity(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError("User must have an email address.")

        email = email.lower()

        user = self.model(
            email=self.normalize_email(email)
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        email = email.lower()

        user = self.create_user(
            email=email,
            password=password
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


# Create your models here.
class User(VersionedEntity, AbstractBaseUser, PermissionsMixin):
    email = models.CharField(max_length=72, unique=True)
    verified_email = models.BooleanField(default=False)

    password = models.CharField(max_length=128)

    account_type = models.CharField(max_length=8, choices=ACCOUNT_TYPE, default='u')

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )

    first_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)

    birthday = models.DateField(null=True, blank=True)

    bio = models.TextField(null=True, blank=True)

    profile_image_s3 = models.CharField(max_length=32, null=True, blank=True)

    provider = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True)

    USERNAME_FIELD = "email"

    objects = UserManager()

    def __str__(self):
        name = ""
        if self.first_name is not None:
            name += f"{self.first_name}"
        if self.last_name is not None:
            name += f" {self.last_name}"
        return f"{self.email}{' (' + name + ')' if name else ''}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class EmailVerificationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=88, unique=True)


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=88, unique=True)
    expires = models.DateTimeField(default=in_three_days)


class SessionToken(models.Model):
    # Tokens for OpenTok sessions
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=SESSION_TOKEN_LENGTH, unique=True)
    expires = models.DateTimeField(null=True, blank=True)


class AvailabilitySchedule(VersionedEntity):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    days_of_week = models.IntegerField()


class AppointmentRequest(VersionedEntity):
    patient = models.ForeignKey(User, on_delete=models.PROTECT, related_name="appointment_requests_as_patient")
    provider = models.ForeignKey(User, on_delete=models.PROTECT, related_name="appointment_requests_as_provider")

    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField()


class ProviderRequest(VersionedEntity):
    patient = models.ForeignKey(User, on_delete=models.PROTECT, related_name="provider_requests_as_patient")
    provider = models.ForeignKey(User, on_delete=models.PROTECT, related_name="provider_requests_as_provider")


class Appointment(VersionedEntity):
    patient = models.ForeignKey(User, on_delete=models.PROTECT, related_name="appointments_as_patient")
    provider = models.ForeignKey(User, on_delete=models.PROTECT, related_name="appointments_as_provider")

    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField()

    ot_session_id = models.CharField(max_length=128, unique=True, null=True, blank=True)

    canceled = models.BooleanField(default=False)

    explicitly_ended = models.BooleanField(default=False)


class RelatedUserField(serializers.RelatedField):
    def to_representation(self, user: Optional[User]):
        if user is None:
            return None

        return {
            "uuid": user.uuid,
            "first_name": user.first_name,
            "last_name": user.last_name
        }