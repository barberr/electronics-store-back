from django import forms
from django.contrib import admin
from django.db import models as django_models
from django.db.models import Count, Min
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, Brand, Product, ProductImage, ProductVariant, Attribute, Order, OrderItem, HeroBlock

# =============== КАТЕГОРИИ ===============
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_header_menu', 'parent', 'created_at']
    list_filter = ['parent', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    fields = ['name', 'slug', 'parent', 'description', 'is_header_menu', 'order', 'image']


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
    extra = 0
    fields = ['image_preview', 'image', 'alt_text', 'order']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="max-height: 64px; border-radius: 6px;" />',
                obj.image.url,
            )
        return '—'
    image_preview.short_description = 'Превью'


# =============== ВАРИАНТЫ ТОВАРА (INLINE) ===============
class ProductVariantAdminForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = '__all__'
        widgets = {
            'attributes': forms.Textarea(
                attrs={
                    'rows': 4,
                    'cols': 60,
                    'style': 'font-family: monospace;',
                }
            ),
        }
        help_texts = {
            'attributes': 'JSON, например: {"color": "Black", "storage": "256GB"}',
        }


class ProductVariantInline(admin.StackedInline):
    model = ProductVariant
    form = ProductVariantAdminForm
    extra = 1
    fields = [
        ('sku', 'is_active'),
        ('price', 'old_price', 'discount_percent'),
        ('stock', 'stock_status'),
        'attributes',
    ]
    readonly_fields = ['discount_percent', 'stock_status']
    verbose_name = 'Вариант товара'
    verbose_name_plural = 'Варианты товара'

    formfield_overrides = {
        django_models.JSONField: {
            'widget': forms.Textarea(
                attrs={
                    'rows': 4,
                    'cols': 60,
                    'style': 'font-family: monospace;',
                }
            ),
        },
    }

    def discount_percent(self, obj):
        if not obj.pk or not obj.old_price or obj.old_price <= obj.price:
            return '—'

        discount = int(round((1 - (obj.price / obj.old_price)) * 100))
        return format_html(
            '<span style="color: #b91c1c; font-weight: 600;">-{}%</span>',
            discount,
        )
    discount_percent.short_description = 'Скидка'

    def stock_status(self, obj):
        if not obj.pk:
            return 'Будет рассчитан после сохранения'
        if obj.stock == 0:
            return mark_safe('<span style="color: #b91c1c; font-weight: 600;">Нет в наличии</span>')
        if obj.stock <= 3:
            return mark_safe('<span style="color: #b45309; font-weight: 600;">Заканчивается</span>')
        return mark_safe('<span style="color: #15803d; font-weight: 600;">В наличии</span>')
    stock_status.short_description = 'Статус остатка'


# =============== ТОВАРЫ ===============
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'product_preview',
        'name',
        'category',
        'brand',
        'price_range',
        'variants_count',
        'is_active',
        'is_popular',
        'created_at'
    ]
    list_filter = [
        ('category', admin.RelatedOnlyFieldListFilter),
        ('brand', admin.RelatedOnlyFieldListFilter),
        'is_active',
        'is_popular',
    ]
    search_fields = ['name', 'slug', 'brand__name', 'category__name', 'variants__sku']
    prepopulated_fields = {'slug': ('name',)}
    list_select_related = ['category', 'brand']
    autocomplete_fields = ['category', 'brand']
    readonly_fields = ['created_at', 'updated_at', 'product_preview', 'variants_summary']
    ordering = ['-created_at']
    list_per_page = 25
    save_on_top = True
    
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'slug', 'category', 'brand', 'product_preview')
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
            'fields': ('is_active', 'is_preorder', 'is_popular', 'warranty_months')
        }),
        ('Сводка', {
            'fields': ('variants_summary', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ProductImageInline, ProductVariantInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('category', 'brand').annotate(
            variants_total=Count('variants', distinct=True),
            min_variant_price=Min('variants__price'),
        )

    def product_preview(self, obj):
        first_image = obj.images.order_by('order', 'id').first()
        if first_image and first_image.image:
            return format_html(
                '<img src="{}" style="max-height: 52px; border-radius: 6px;" />',
                first_image.image.url,
            )
        return '—'
    product_preview.short_description = 'Фото'

    def price_range(self, obj):
        if obj.min_variant_price is None:
            return '—'
        return f'от {obj.min_variant_price:.2f} ₽'
    price_range.short_description = 'Цена'
    price_range.admin_order_field = 'min_variant_price'

    def variants_count(self, obj):
        return obj.variants_total
    variants_count.short_description = 'Вариантов'
    variants_count.admin_order_field = 'variants_total'

    def stock_total(self, obj):
        return sum(variant.stock for variant in obj.variants.all())
    stock_total.short_description = 'Остаток'

    def variants_summary(self, obj):
        variants = obj.variants.order_by('id')
        if not variants.exists():
            return 'Варианты не добавлены'

        rows = ['<ul style="margin:0; padding-left:18px;">']
        for variant in variants:
            label = variant.sku or 'Без SKU'
            attrs = ', '.join(f'{k}: {v}' for k, v in variant.attributes.items()) or 'без атрибутов'
            rows.append(
                f'<li>{label} • {attrs} • {variant.price:.2f} ₽ • остаток {variant.stock}</li>'
            )
        rows.append('</ul>')
        return mark_safe(''.join(rows))
    variants_summary.short_description = 'Варианты товара'


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

@admin.register(HeroBlock)
class HeroBlockAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'is_active', 'order', 'published_at']
    list_filter = ['status', 'is_active', 'published_at']
    search_fields = ['title', 'subtitle', 'description']
    list_editable = ['order', 'is_active']
    date_hierarchy = 'published_at'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'subtitle', 'description', 'video_mp4', 'image', 'background_image')
        }),
        ('Настройки отображения', {
            'fields': ('background_color', 'text_color', 'button_text', 'button_link')
        }),
        ('Статус и публикация', {
            'fields': ('status', 'is_active', 'order', 'published_at')
        }),
        ('Связи', {
            'fields': ('product',)
        }),
    )
