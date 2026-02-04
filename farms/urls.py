# farms/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SoilTypeViewSet,
    CropTypeViewSet,
    PlantationTypeViewSet,
    PlantingMethodViewSet,
    FarmViewSet,
    PlotViewSet,
    FarmImageViewSet,
    FarmSensorViewSet,
    FarmIrrigationViewSet,
    GrapseReportViewSet,  # <-- add this
)

router = DefaultRouter()
router.register('soil-types',       SoilTypeViewSet,        basename='soiltype')
router.register('crop-types',       CropTypeViewSet,        basename='croptype')
router.register('plantation-types', PlantationTypeViewSet,  basename='plantationtype')
router.register('planting-methods', PlantingMethodViewSet,  basename='plantingmethod')
router.register('farms',            FarmViewSet,            basename='farm')
router.register('plots',            PlotViewSet,            basename='plot')
router.register('farm-images',      FarmImageViewSet,       basename='farmimage')
router.register('farm-sensors',     FarmSensorViewSet,      basename='farmsensor')
router.register('farm-irrigations', FarmIrrigationViewSet,  basename='farmirrigation')
router.register('grapse-reports',   GrapseReportViewSet,    basename='grapsereport')  # <-- new

urlpatterns = [
    path('', include(router.urls)),
]
