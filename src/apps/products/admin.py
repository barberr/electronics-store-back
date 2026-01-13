from django.contrib import admin
from .models import Category, Brand, Product, ProductImage, ProductVariant, Attribute, Order, OrderItem

# =============== КАТЕГОРИИ ===============
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'created_at']
    list_filter = ['parent', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    fields = ['name', 'slug', 'parent', 'description', 'image']


# =============== БРЕНДЫ ===============
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'logo', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    fields = ['name', 'slug', 'logo']


# =============== АТРИБУТЫ ===============
@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'type', 'values']
    list_filter = ['type']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    fields = ['name', 'slug', 'type', 'values']


# =============== ИЗОБРАЖЕНИЯ ТОВАРА (INLINE) ===============
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'order']


# =============== ВАРИАНТЫ ТОВАРА (INLINE) ===============
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['sku', 'attributes', 'price', 'old_price', 'is_active', 'stock']


# =============== ТОВАРЫ ===============
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'category', 
        'brand',
        'is_active',
        'is_preorder',
        'warranty_months',
        'created_at'
    ]
    list_filter = [
        'category', 
        'brand',
        'is_active',
        'is_preorder',
        'warranty_months',
        'created_at'
    ]
    search_fields = ['name', 'sku', 'brand__name', 'category__name']
    prepopulated_fields = {'slug': ('name',)}
    
    # Группировка полей
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'slug', 'category', 'brand')
        }),
        ('Описание', {
            'fields': ('short_description', 'description', 'delivery_text'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('seo_title', 'seo_description'),
            'classes': ('collapse',)
        }),
        ('Настройки', {
            'fields': ('is_active', 'is_preorder', 'warranty_months')
        }),
    )
    
    inlines = [ProductImageInline, ProductVariantInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['price_at_time']
    fields = ['variant', 'quantity', 'price_at_time']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'contact_name', 'contact_phone', 'user', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['contact_name', 'contact_phone', 'user__username']
    readonly_fields = ['created_at']
    inlines = [OrderItemInline]
    
    # Запретить редактирование, если нужно (только просмотр)
    # def has_add_permission(self, request):
    #     return False
    # def has_change_permission(self, request, obj=None):
    #     return False