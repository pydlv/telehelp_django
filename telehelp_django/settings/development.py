from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '@x%ss&+kq@5ra94s4w)y#0i%m-zadk^bbd#upgo+j8k!)zfq41'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

RUNNING_DEVSERVER = (len(sys.argv) > 1 and sys.argv[1] == 'runserver')

ALLOWED_HOSTS = ["172.26.5.185", "127.0.0.1"]


# Email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = "affordabletmh@gmail.com"
EMAIL_HOST_PASSWORD = "UjJ#W+9Hma[|^]N.J("


# Push Notifications
PUSH_NOTIFICATIONS_SETTINGS = {
    # Load and process all PUSH_NOTIFICATIONS_SETTINGS using the AppConfig manager.
    "CONFIG": "push_notifications.conf.AppConfig",

    "UPDATE_ON_DUPLICATE_REG_ID": True,

    # collection of all defined applications
    "APPLICATIONS": {
        "telehelp_push_fcm": {
            # PLATFORM (required) determines what additional settings are required.
            "PLATFORM": "FCM",

            # required FCM setting
            "API_KEY": "AAAANVO1_XE:APA91bF3p4vfxvIQRt4JMtP0HK8YbrE7J0tHQgRCYdKJCEWewbgquGlOrpez1NnzdIP6REbkuFbtDM0erdI"
                       "kng7Vqnij3VnUTA7mLqRREDxwbVGmW6Qbd88gpZ3O4vBr5muSw8-b1zeI",
        },
        "telehelp_push_apns": {
            # PLATFORM (required) determines what additional settings are required.
            "PLATFORM": "APNS",

            # required APNS setting
            "CERTIFICATE": "./telehelp_django/settings/certs/aps-dev.pem",

            "USE_SANDBOX": True
        }
    }
}


# Log settings
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/django_debug.log',
        },
        'console': {
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}

if DEBUG:
    # make all loggers use the console.
    for logger in LOGGING['loggers']:
        LOGGING['loggers'][logger]['handlers'] = ['console']
