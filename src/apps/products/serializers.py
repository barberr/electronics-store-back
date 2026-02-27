from rest_framework import serializers
from .models import Category, Brand, Product, ProductImage, ProductVariant, Attribute, Order, HeroBlock

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'description', 'image', 'created_at', 'updated_at']

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'logo', 'created_at', 'updated_at']

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'order']

class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ['id', 'name', 'slug', 'type', 'values']

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'attributes', 'price', 'old_price',
            'is_active', 'stock'
        ]

class ProductSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'brand', 'category',
            'short_description', 'description',
            'seo_title', 'seo_description',
            'is_active', 'is_preorder',
            'delivery_text', 'warranty_months',
            'created_at', 'updated_at',
            'images', 'variants'
        ]

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'contact_phone', 'contact_name',
            'contact_dob', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user'] 

class HeroBlockSerializer(serializers.ModelSerializer):
    """Сериализатор для герой-блоков"""
    
    # Опционально: вложенный сериализатор для связанного продукта
    product_slug = serializers.CharField(
        source='product.slug',
        read_only=True
    )

    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )
    
    product_price = serializers.CharField(
        source='product.price',
        read_only=True
    )
    
    class Meta:
        model = HeroBlock
        fields = [
            'id',
            'title',
            'subtitle',
            'description',
            'status',
            'is_active',
            'order',
            'published_at',
            'created_at',
            'updated_at',
            'product',
            'product_name',
            'product_slug',
            'product_price',
            'video_mp4',
            'image',
            'background_image',
            'background_color',
            'text_color',
            'button_text',
            'button_link',
        ]
        read_only_fields = ['created_at', 'updated_at', 'published_at']