from django.urls import path, include
from rest_framework_nested import routers
from .views import InventoryItemViewSet, InventoryTransactionViewSet, StockViewSet

router = routers.DefaultRouter()
router.register('inventory', InventoryItemViewSet)
router.register('transactions', InventoryTransactionViewSet)
router.register('stock', StockViewSet, basename='stock')

urlpatterns = [
    path('', include(router.urls)),
] 