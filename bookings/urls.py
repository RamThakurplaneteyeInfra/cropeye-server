from django.urls import path, include
from rest_framework_nested import routers
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, BookingCommentViewSet, BookingAttachmentViewSet

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')

booking_router = routers.NestedSimpleRouter(router, r'bookings', lookup='booking')
booking_router.register(r'comments', BookingCommentViewSet, basename='booking-comment')
booking_router.register(r'attachments', BookingAttachmentViewSet, basename='booking-attachment')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(booking_router.urls)),
] 