from push_notifications.api.rest_framework import APNSDeviceAuthorizedViewSet, GCMDeviceAuthorizedViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("apns", APNSDeviceAuthorizedViewSet)
router.register("gcm", GCMDeviceAuthorizedViewSet)
