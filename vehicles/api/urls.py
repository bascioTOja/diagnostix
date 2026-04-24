from rest_framework.routers import DefaultRouter

from vehicles.api.views import VehicleViewSet

router = DefaultRouter(trailing_slash=True)
router.register("vehicles", VehicleViewSet, basename="api-vehicle")

urlpatterns = router.urls

