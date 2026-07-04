from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, CartView, CartItemViewSet, DashboardStatsView, SalesReportView

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'cart/items', CartItemViewSet, basename='cart-items')

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('reports/sales/', SalesReportView.as_view(), name='sales-report'),
    path('', include(router.urls)),
]
