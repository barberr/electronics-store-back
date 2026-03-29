from rest_framework import serializers
from .models import Category, Brand, Product, ProductImage, ProductVariant, Attribute, Order, HeroBlock


def serialize_attribute_value(attribute, value):
    return {
        'id': attribute.id,
        'name': attribute.name,
        'slug': attribute.slug,
        'type': attribute.type,
        'applies_to': attribute.applies_to,
        'is_required': attribute.is_required,
        'unit': attribute.unit,
        'group_name': attribute.group_name,
        'value': value,
    }


def get_category_attribute_map(category, applies_to):
    if not category:
        return {}
    return {
        attribute.slug: attribute
        for attribute in category.attributes.filter(applies_to=applies_to).order_by('sort_order', 'name')
    }


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
        fields = [
            'id', 'name', 'slug', 'applies_to', 'type', 'is_required',
            'sort_order', 'unit', 'group_name', 'values',
        ]

class ProductVariantSerializer(serializers.ModelSerializer):
    attribute_values = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'attributes', 'price', 'old_price',
            'is_active', 'stock', 'attribute_values',
        ]

    def get_attribute_values(self, obj):
        product = getattr(obj, 'product', None)
        category = getattr(product, 'category', None)
        attribute_map = get_category_attribute_map(category, 'variant')

        resolved_values = []
        for slug, value in (obj.attributes or {}).items():
            attribute = attribute_map.get(slug)
            if attribute is None:
                resolved_values.append({
                    'id': None,
                    'name': slug,
                    'slug': slug,
                    'type': 'string',
                    'applies_to': 'variant',
                    'is_required': False,
                    'unit': '',
                    'group_name': '',
                    'value': value,
                })
                continue
            resolved_values.append(serialize_attribute_value(attribute, value))
        return resolved_values

class ProductSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    specifications = serializers.SerializerMethodField()
    specifications_map = serializers.JSONField(source='specifications', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'brand', 'category',
            'short_description', 'description',
            'seo_title', 'seo_description',
            'is_active', 'is_preorder',
            'delivery_text', 'warranty_months',
            'created_at', 'updated_at',
            'specifications', 'specifications_map',
            'images', 'variants'
        ]

    def get_specifications(self, obj):
        attribute_map = get_category_attribute_map(obj.category, 'product')

        resolved_values = []
        for slug, value in (obj.specifications or {}).items():
            attribute = attribute_map.get(slug)
            if attribute is None:
                resolved_values.append({
                    'id': None,
                    'name': slug,
                    'slug': slug,
                    'type': 'string',
                    'applies_to': 'product',
                    'is_required': False,
                    'unit': '',
                    'group_name': '',
                    'value': value,
                })
                continue
            resolved_values.append(serialize_attribute_value(attribute, value))
        return resolved_values


class BrandDetailSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'logo', 'created_at', 'updated_at', 'products']

    def get_products(self, obj):
        request = self.context.get('request')
        products = obj.products.filter(is_active=True).select_related(
            'brand',
            'category',
        ).prefetch_related(
            'images',
            'variants',
        )
        return ProductSerializer(products, many=True, context={'request': request}).data

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
