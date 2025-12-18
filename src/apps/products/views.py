from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category, Product, Brand
from .serializers import CategorySerializer, ProductSerializer, BrandSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    @action(detail=True, methods=['get'], url_path='products')
    def products(self, request, pk=None):
        """Возвращает товары категории по её ID"""
        try:
            category = self.get_object()  # получает Category по pk
            products = Product.objects.filter(category=category)
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return Product.objects.filter(is_available=True).select_related('category')


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    @action(detail=True, methods=['get'], url_path='products')
    def products(self, request, pk=None):
        """Возвращает товары бренда по его ID"""
        try:
            brand = self.get_object()  # получает Category по pk
            products = Product.objects.filter(brand=brand)
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)
        except Brand.DoesNotExist:
            return Response({'error': 'Brand not found'}, status=status.HTTP_404_NOT_FOUND)