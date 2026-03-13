from rest_framework import serializers
from django.core.validators import MinValueValidator
from django.apps import apps
from .models import Cart, CartItem


# Получаем модель из приложения products
def get_product_variant_model():
    return apps.get_model('products', 'ProductVariant')


class CartItemSerializer(serializers.ModelSerializer):
    """Сериализатор для элемента корзины"""
    
    variant_name = serializers.CharField(source='variant.product.name', read_only=True)
    variant_attributes = serializers.JSONField(source='variant.attributes', read_only=True)
    variant_price = serializers.DecimalField(
        source='variant.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    variant_image = serializers.SerializerMethodField()
    total_price = serializers.DecimalField(
        source='get_total_price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'variant', 'variant_name', 'variant_attributes',
            'variant_price', 'variant_image', 'quantity', 'total_price',
            'added_at'
        ]
        read_only_fields = ['id', 'added_at']
    
    def get_variant_image(self, obj):
        """Получить изображение варианта товара"""
        if obj.variant.product.images.exists():
            return obj.variant.product.images.first().image.url
        return None
    
    def validate_quantity(self, value):
        """Проверка доступного количества"""
        variant_id = self.initial_data.get('variant')
        if variant_id:
            ProductVariant = get_product_variant_model()
            try:
                variant = ProductVariant.objects.get(id=variant_id)
                if value > variant.stock:
                    raise serializers.ValidationError(
                        f"Недостаточно товара на складе. Доступно: {variant.stock}"
                    )
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError("Вариант товара не найден")
        return value


class CartSerializer(serializers.ModelSerializer):
    """Сериализатор для корзины"""
    
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(source='get_total_items', read_only=True)
    total_price = serializers.DecimalField(
        source='get_total_price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = Cart
        fields = [
            'id', 'status', 'items', 'total_items',
            'total_price', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CartAddItemSerializer(serializers.Serializer):
    """Сериализатор для добавления товара в корзину"""
    
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(
        default=1,
        validators=[MinValueValidator(1)]  # ← Теперь импортировано правильно
    )
    
    def validate_variant_id(self, value):
        """Проверка существования варианта"""
        ProductVariant = get_product_variant_model()
        try:
            variant = ProductVariant.objects.get(id=value)
            if not variant.is_active:
                raise serializers.ValidationError("Этот вариант товара не активен")
            return value
        except ProductVariant.DoesNotExist:
            raise serializers.ValidationError("Вариант товара не найден")


class CartUpdateItemSerializer(serializers.Serializer):
    """Сериализатор для обновления количества товара в корзине"""
    
    quantity = serializers.IntegerField(
        validators=[MinValueValidator(1)]  # ← Теперь импортировано правильно
    )
