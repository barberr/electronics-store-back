from django.db.models import Q
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Category, Brand, Product, ProductVariant, Attribute, Order, HeroBlock
from .serializers import (
    CategorySerializer, BrandSerializer, ProductSerializer,
    ProductVariantSerializer, AttributeSerializer, OrderSerializer, HeroBlockSerializer
)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'

    @action(detail=False, methods=['get'], url_path='header-menu')
    def header_menu_categories(self, request):
        """
        Возвращает только категории, отмеченные для отображения в верхнем меню (is_header_menu=True)
        """
        categories = Category.objects.filter(is_header_menu=True).order_by('order')
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)


    @action(detail=True, methods=['get'], url_path='products')
    def products(self, request, slug=None):
        category = self.get_object()
        products = Product.objects.filter(category=category, is_active=True)
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related(
            'brand',
            'category',
        ).prefetch_related(
            'images',
            'variants',
        )

    @action(detail=False, methods=['get'], url_path='popular')
    def popular_products(self, request):
        """
        Возвращает только товары, отмеченные для отображения в популярном (is_popular=True)
        """
        products = self.get_queryset().filter(is_popular=True)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response(
                {'detail': 'Query parameter "q" is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        products = self.get_queryset().filter(
            Q(name__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
            | Q(brand__name__icontains=query)
            | Q(category__name__icontains=query)
            | Q(variants__sku__icontains=query)
        ).distinct()

        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    lookup_field = 'slug'

    @action(detail=True, methods=['get'], url_path='products')
    def products(self, request, slug=None):
        brand = self.get_object()
        products = Product.objects.filter(brand=brand, is_active=True)
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

class ProductVariantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductVariant.objects.filter(is_active=True).select_related('product')
    serializer_class = ProductVariantSerializer
    lookup_field = 'sku'

class AttributeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer
    lookup_field = 'slug'

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user)
        return Order.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OverviewViewSet(viewsets.GenericViewSet):
    """
    ViewSet для агрегированного представления каталога.
    Поддерживает только один эндпоинт — list (GET /api/v1/overview/).
    """
    
    # Не требует queryset по умолчанию, т.к. агрегирует данные вручную
    pagination_class = None  # отключаем пагинацию для overview

    def list(self, request, *args, **kwargs):
        """
        GET /api/v1/overview/
        Возвращает:
        - brands: все бренды
        - categories: все категории
        - catalog: товары, сгруппированные по категориям (сохраняя порядок категорий)
        """
        # 1. Получаем все данные с оптимизацией запросов
        brands = Brand.objects.all()
        categories = Category.objects.all().order_by('id')  # или order_by('name'), как в Meta
        # Желательно select_related, чтобы избежать N+1 при сериализации
        products = Product.objects.select_related('brand', 'category') \
                                   .filter(is_active=True) \
                                   .order_by('category_id', '-created_at')

        # 2. Сериализуем бренды и категории
        brand_data = BrandSerializer(brands, many=True, context={'request': request}).data
        category_data = CategorySerializer(categories, many=True, context={'request': request}).data

        # 3. Группируем товары по категориям
        # Создаём маппинг: category_id → список товаров
        products_by_category = {}
        for category in categories:
            products_by_category[category.id] = []

        for product in products:
            products_by_category[product.category_id].append(
                ProductSerializer(product, context={'request': request}).data
            )

        # 4. Формируем упорядоченный каталог
        catalog = []
        for cat in categories:
            catalog.append({
                'id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
                'products': products_by_category[cat.id]
            })

        return Response({
            'brands': brand_data,
            'categories': category_data,
            'catalog': catalog,
        })

class HeroBlockViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления герой-блоками.
    """
    
    serializer_class = HeroBlockSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """
        Возвращает только опубликованные и активные блоки для неавторизованных пользователей.
        Для авторизованных — все блоки.
        """
        if self.request.user.is_authenticated:
            return HeroBlock.objects.all()
        return HeroBlock.objects.filter(
            status='published',
            is_active=True
        )
