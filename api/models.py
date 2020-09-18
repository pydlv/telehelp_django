import uuid as uuid
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
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

        user = self.model(
            email=self.normalize_email(email)
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
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

    first_name = models.CharField(max_length=30, null=True)
    last_name = models.CharField(max_length=30, null=True)

    birthday = models.DateField(null=True)

    bio = models.TextField(null=True)

    profile_image_s3 = models.CharField(max_length=32, null=True)

    provider = models.ForeignKey("self", on_delete=models.PROTECT, null=True)

    USERNAME_FIELD = "email"

    objects = UserManager()

    def __str__(self):
        return self.email

    # def has_perm(self, perm, obj=None):
    #     return self.is_admin


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
    expires = models.DateTimeField(null=True)


class AvailabilitySchedule(VersionedEntity):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    days_of_week = models.IntegerField()


class Appointment(VersionedEntity):
    patient = models.ForeignKey(User, on_delete=models.PROTECT, related_name="appointments_as_patient")
    provider = models.ForeignKey(User, on_delete=models.PROTECT, related_name="appointments_as_provider")

    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField()

    ot_session_id = models.CharField(max_length=128, unique=True, null=True)

    canceled = models.BooleanField(default=False)

    explicitly_ended = models.BooleanField(default=False)