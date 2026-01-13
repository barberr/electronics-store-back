# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, BrandViewSet, ProductViewSet,
    ProductVariantViewSet, AttributeViewSet,
    OrderViewSet, OverviewViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'variants', ProductVariantViewSet, basename='variant')
router.register(r'attributes', AttributeViewSet, basename='attribute')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'overview', OverviewViewSet, basename='overview')

urlpatterns = [
    path('', include(router.urls)),
]