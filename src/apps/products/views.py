from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category, Product, Brand
from .serializers import CategorySerializer, ProductSerializer, BrandSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'

    @action(detail=True, methods=['get'], url_path='products')
    def products(self, request, slug=None):
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
                                   .filter(is_available=True) \
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