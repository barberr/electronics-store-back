from django import forms
from django.contrib import admin
from django.db.models import Count, Min
from django.forms.models import BaseInlineFormSet
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from decimal import Decimal
from .models import Category, Brand, Product, ProductImage, ProductVariant, Attribute, Order, OrderItem, HeroBlock


SPEC_FIELD_PREFIX = 'spec__'
VARIANT_FIELD_PREFIX = 'attr__'


def build_attribute_form_field(attribute, required=None):
    required = attribute.is_required if required is None else required
    label = attribute.name if not attribute.unit else f'{attribute.name}, {attribute.unit}'

    if attribute.type == 'enum':
        choices = [('', '---------')]
        choices.extend((value, value) for value in (attribute.values or []))
        return forms.ChoiceField(label=label, choices=choices, required=required)

    if attribute.type == 'number':
        return forms.DecimalField(label=label, required=required, decimal_places=2)

    return forms.CharField(label=label, required=required)


def get_category_attributes(category, applies_to):
    if not category:
        return []
    return list(category.attributes.filter(applies_to=applies_to).order_by('sort_order', 'name'))


def get_category_color_attribute(category):
    if not category:
        return None
    return category.attributes.filter(
        applies_to='variant',
        slug='color',
        type='enum',
    ).first()


def get_color_value_choices(category, current_value=''):
    color_attribute = get_category_color_attribute(category)
    choices = [('', '---------')]

    if color_attribute:
        choices.extend((value, value) for value in (color_attribute.values or []))

    if current_value and current_value not in {choice_value for choice_value, _ in choices}:
        choices.append((current_value, current_value))

    return choices


def normalize_attribute_value(value):
    if isinstance(value, Decimal):
        return format(value, 'f')
    return value


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['specifications']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_attributes = getattr(self, 'product_attributes', [])
        category = getattr(self, 'resolved_category', None) or self._resolve_category()

        if category and not self.product_attributes:
            self.product_attributes = get_category_attributes(category, 'product')

        current_specs = self.instance.specifications or {}
        for attribute in self.product_attributes:
            field_name = f'{SPEC_FIELD_PREFIX}{attribute.slug}'
            if field_name not in self.fields:
                self.fields[field_name] = build_attribute_form_field(attribute)
            self.fields[field_name].initial = current_specs.get(attribute.slug)

    def _resolve_category(self):
        category_id = None
        if self.is_bound:
            category_id = self.data.get('category')
        elif self.instance and self.instance.category_id:
            category_id = self.instance.category_id
        else:
            category_id = self.initial.get('category')

        if not category_id:
            return None

        try:
            return Category.objects.get(pk=category_id)
        except (Category.DoesNotExist, ValueError, TypeError):
            return None

    def clean(self):
        cleaned_data = super().clean()

        if not self.product_attributes:
            cleaned_data['specifications'] = self.instance.specifications or {}
            return cleaned_data

        cleaned_data['specifications'] = {
            attribute.slug: normalize_attribute_value(cleaned_data.get(f'{SPEC_FIELD_PREFIX}{attribute.slug}'))
            for attribute in self.product_attributes
            if cleaned_data.get(f'{SPEC_FIELD_PREFIX}{attribute.slug}') not in (None, '')
        }
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.specifications = self.cleaned_data.get('specifications', {})
        if commit:
            instance.save()
            self.save_m2m()
        return instance

# =============== КАТЕГОРИИ ===============
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_header_menu', 'parent', 'created_at']
    list_filter = ['parent', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['attributes']
    fields = ['name', 'slug', 'parent', 'description', 'is_header_menu', 'order', 'image', 'attributes']


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
    list_display = ['name', 'slug', 'applies_to', 'type', 'is_required', 'sort_order']
    list_filter = ['applies_to', 'type', 'is_required']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    fields = ['name', 'slug', 'applies_to', 'type', 'is_required', 'sort_order', 'group_name', 'unit', 'values']


# =============== ИЗОБРАЖЕНИЯ ТОВАРА (INLINE) ===============
class ProductImageAdminForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = '__all__'

    def __init__(self, *args, category=None, **kwargs):
        self.category = category or getattr(self, 'resolved_category', None)
        super().__init__(*args, **kwargs)

        current_value = self.instance.color_value if self.instance else ''
        self.fields['color_value'] = forms.ChoiceField(
            label='Цвет варианта',
            required=False,
            choices=get_color_value_choices(self.category, current_value=current_value),
            help_text='Значения берутся из variant-атрибута color. Пустое значение означает медиа для всех цветов.',
        )
        self.fields['color_value'].initial = current_value


class ProductImageInlineFormSet(BaseInlineFormSet):
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['category'] = getattr(self.instance, 'category', None)
        return kwargs


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    form = ProductImageAdminForm
    formset = ProductImageInlineFormSet
    extra = 0
    fields = ['image_preview', 'image', 'color_value', 'alt_text', 'order']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.pk and obj.image:
            if obj.media_type == 'video':
                return format_html(
                    '<video src="{}" style="max-height: 64px; border-radius: 6px;" controls muted preload="metadata"></video>',
                    obj.image.url,
                )
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
        exclude = ['attributes']

    def __init__(self, *args, category=None, **kwargs):
        self.category = category or getattr(self, 'resolved_category', None)
        super().__init__(*args, **kwargs)
        self.variant_attributes = getattr(self, 'variant_attributes', [])
        if self.category and not self.variant_attributes:
            self.variant_attributes = get_category_attributes(self.category, 'variant')

        current_attributes = self.instance.attributes or {}
        for attribute in self.variant_attributes:
            field_name = f'{VARIANT_FIELD_PREFIX}{attribute.slug}'
            if field_name not in self.fields:
                self.fields[field_name] = build_attribute_form_field(attribute)
            self.fields[field_name].initial = current_attributes.get(attribute.slug)

    def clean(self):
        cleaned_data = super().clean()

        if not self.variant_attributes:
            cleaned_data['attributes'] = self.instance.attributes or {}
            return cleaned_data

        cleaned_data['attributes'] = {
            attribute.slug: normalize_attribute_value(cleaned_data.get(f'{VARIANT_FIELD_PREFIX}{attribute.slug}'))
            for attribute in self.variant_attributes
            if cleaned_data.get(f'{VARIANT_FIELD_PREFIX}{attribute.slug}') not in (None, '')
        }
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.attributes = self.cleaned_data.get('attributes', {})
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ProductVariantInlineFormSet(BaseInlineFormSet):
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['category'] = getattr(self.instance, 'category', None)
        return kwargs


class ProductVariantInline(admin.StackedInline):
    model = ProductVariant
    form = ProductVariantAdminForm
    formset = ProductVariantInlineFormSet
    extra = 1
    readonly_fields = ['discount_percent', 'stock_status']
    verbose_name = 'Вариант товара'
    verbose_name_plural = 'Варианты товара'

    def get_extra(self, request, obj=None, **kwargs):
        if obj is None or obj.category_id is None:
            return 0
        return super().get_extra(request, obj, **kwargs)

    def get_fields(self, request, obj=None):
        fields = [
            ('sku', 'is_active'),
            ('price', 'old_price', 'discount_percent'),
            ('stock', 'stock_status'),
        ]
        for attribute in get_category_attributes(getattr(obj, 'category', None), 'variant'):
            fields.append(f'{VARIANT_FIELD_PREFIX}{attribute.slug}')
        return fields

    def get_formset(self, request, obj=None, **kwargs):
        variant_attributes = get_category_attributes(getattr(obj, 'category', None), 'variant')
        dynamic_form_attrs = {
            'variant_attributes': variant_attributes,
            'resolved_category': getattr(obj, 'category', None),
        }
        for attribute in variant_attributes:
            field_name = f'{VARIANT_FIELD_PREFIX}{attribute.slug}'
            dynamic_form_attrs[field_name] = build_attribute_form_field(attribute)

        kwargs['form'] = type(
            'DynamicProductVariantAdminForm',
            (self.form,),
            dynamic_form_attrs,
        )
        formset = super().get_formset(request, obj, **kwargs)
        return formset

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
    form = ProductAdminForm
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
    readonly_fields = ['created_at', 'updated_at', 'product_preview', 'variants_summary', 'category_attributes_hint']
    ordering = ['-created_at']
    list_per_page = 25
    save_on_top = True
    
    inlines = [ProductImageInline, ProductVariantInline]

    def get_fieldsets(self, request, obj=None):
        category = self._resolve_category(request, obj)
        product_attribute_fields = [
            f'{SPEC_FIELD_PREFIX}{attribute.slug}'
            for attribute in get_category_attributes(category, 'product')
        ]

        return (
            ('Основное', {
                'fields': ('name', 'slug', 'category', 'brand', 'product_preview')
            }),
            ('Описание', {
                'fields': ('short_description', 'description', 'delivery_text'),
                'classes': ('collapse',)
            }),
            ('Характеристики товара', {
                'fields': tuple(product_attribute_fields or ['category_attributes_hint']),
                'classes': ('collapse',),
                'description': 'После выбора категории и сохранения товара здесь появятся подходящие характеристики.',
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

    def _resolve_category(self, request, obj=None):
        category_id = request.POST.get('category') or request.GET.get('category')
        if not category_id and obj is not None:
            category_id = obj.category_id

        if not category_id:
            return None

        try:
            return Category.objects.get(pk=category_id)
        except (Category.DoesNotExist, ValueError, TypeError):
            return None

    def get_form(self, request, obj=None, change=False, **kwargs):
        category = self._resolve_category(request, obj)
        product_attributes = get_category_attributes(category, 'product')

        if 'fields' not in kwargs:
            kwargs['fields'] = forms.ALL_FIELDS

        dynamic_form_attrs = {
            'product_attributes': product_attributes,
            'resolved_category': category,
        }
        for attribute in product_attributes:
            field_name = f'{SPEC_FIELD_PREFIX}{attribute.slug}'
            dynamic_form_attrs[field_name] = build_attribute_form_field(attribute)

        kwargs['form'] = type(
            'DynamicProductAdminForm',
            (self.form,),
            dynamic_form_attrs,
        )

        return super().get_form(request, obj, change=change, **kwargs)

    def category_attributes_hint(self, obj):
        if obj and obj.category_id:
            return 'Для этой категории пока не настроены общие характеристики.'
        return 'Сначала выберите категорию и сохраните товар, затем появятся нужные поля характеристик и варианты.'
    category_attributes_hint.short_description = 'Подсказка'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('category', 'brand').annotate(
            variants_total=Count('variants', distinct=True),
            min_variant_price=Min('variants__price'),
        )

    def product_preview(self, obj):
        first_image = obj.images.order_by('order', 'id').first()
        if first_image and first_image.image:
            if first_image.media_type == 'video':
                return format_html(
                    '<video src="{}" style="max-height: 52px; border-radius: 6px;" muted preload="metadata"></video>',
                    first_image.image.url,
                )
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
