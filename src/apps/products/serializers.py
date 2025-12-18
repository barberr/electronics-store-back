from rest_framework import serializers
from .models import Category, Product, ProductImage

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_main']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
        source='category'
    )
    images = ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'category', 'category_id',
            'description', 'price', 'stock', 'is_available',
            'created_at', 'updated_at', 'images'
        ]