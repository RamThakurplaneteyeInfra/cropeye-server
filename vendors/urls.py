from django.urls import path, include
from rest_framework_nested import routers
from .views import (
    VendorViewSet, 
    PurchaseOrderViewSet, 
    PurchaseOrderItemViewSet,
    VendorCommunicationViewSet,
    OrderViewSet
)

router = routers.DefaultRouter()
router.register('vendors', VendorViewSet)
router.register('purchase-orders', PurchaseOrderViewSet)
router.register('purchase-order-items', PurchaseOrderItemViewSet)
router.register('vendor-communications', VendorCommunicationViewSet)
router.register('orders', OrderViewSet, basename='order')

# Nested routes for purchase orders under vendors
vendors_router = routers.NestedDefaultRouter(router, 'vendors', lookup='vendor')
vendors_router.register('purchase-orders', PurchaseOrderViewSet, basename='vendor-purchase-orders')
vendors_router.register('communications', VendorCommunicationViewSet, basename='vendor-communications')

# Nested routes for items under purchase orders
purchase_orders_router = routers.NestedDefaultRouter(router, 'purchase-orders', lookup='purchase_order')
purchase_orders_router.register('items', PurchaseOrderItemViewSet, basename='purchase-order-items')
purchase_orders_router.register('communications', VendorCommunicationViewSet, basename='purchase-order-communications')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(vendors_router.urls)),
    path('', include(purchase_orders_router.urls)),
] 