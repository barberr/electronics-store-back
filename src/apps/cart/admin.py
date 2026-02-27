from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    """Инлайн для отображения элементов корзины внутри корзины"""
    
    model = CartItem
    extra = 0
    readonly_fields = ['variant', 'quantity', 'added_at', 'get_total_price', 'get_variant_stock']
    fields = ['variant', 'quantity', 'get_variant_stock', 'get_total_price', 'added_at']
    can_delete = True
    show_change_link = True
    
    def get_total_price(self, obj):
        """Отобразить общую стоимость элемента"""
        total = obj.get_total_price()
        return f"{total:,.2f} ₽"
    get_total_price.short_description = 'Стоимость'
    get_total_price.admin_order_field = 'quantity'
    
    def get_variant_stock(self, obj):
        """Отобразить остаток товара"""
        return obj.variant.stock
    get_variant_stock.short_description = 'Остаток на складе'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Админка для корзины"""
    
    list_display = [
        'id',
        'get_user_or_session',
        'status',
        'get_total_items',
        'get_total_price',
        'created_at',
        'updated_at',
        'status_badge'
    ]
    
    list_filter = [
        'status',
        'created_at',
        'updated_at'
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'session_key'
    ]
    
    readonly_fields = [
        'user',
        'session_key',
        'created_at',
        'updated_at',
        'get_total_items',
        'get_total_price',
        'get_cart_details'
    ]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'session_key', 'status')
        }),
        ('Статистика', {
            'fields': ('get_total_items', 'get_total_price', 'get_cart_details')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [CartItemInline]
    
    actions = ['mark_as_completed', 'mark_as_abandoned', 'clear_carts']
    
    def get_user_or_session(self, obj):
        """Отобразить пользователя или сессию"""
        if obj.user:
            return format_html(
                '<span style="color: green; font-weight: bold;">👤 {}</span>',
                obj.user.username
            )
        return format_html(
            '<span style="color: gray;">📱 Сессия: {}</span>',
            (obj.session_key[:15] + '...') if obj.session_key else '—'
        )
    get_user_or_session.short_description = 'Пользователь / Сессия'
    get_user_or_session.admin_order_field = 'user'
    
    def get_total_items(self, obj):
        """Отобразить общее количество товаров"""
        count = obj.get_total_items()
        if count == 0:
            return mark_safe('<span style="color: red;">Пусто</span>')
        return format_html(
            '<span style="color: blue; font-weight: bold;">{}</span>',
            count
        )
    get_total_items.short_description = 'Товаров'
    
    def get_total_price(self, obj):
        """Отобразить общую стоимость"""
        total = obj.get_total_price()
        formatted_total = f"{total:.2f}"
        return format_html(
            '<span style="color: #ef4444; font-weight: bold; font-size: 1.1em;">{} ₽</span>',
            formatted_total
        )
    get_total_price.short_description = 'Сумма'
    
    def get_cart_details(self, obj):
        """Отобразить детали корзины"""
        items = obj.items.all()
        if not items:
            return "Корзина пуста"
        
        html = '<div style="max-height: 300px; overflow-y: auto;">'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background-color: #f3f4f6;"><th style="padding: 8px; text-align: left; border-bottom: 2px solid #e5e7eb;">Товар</th><th style="padding: 8px; text-align: left; border-bottom: 2px solid #e5e7eb;">Кол-во</th><th style="padding: 8px; text-align: right; border-bottom: 2px solid #e5e7eb;">Цена</th><th style="padding: 8px; text-align: right; border-bottom: 2px solid #e5e7eb;">Итого</th></tr>'
        
        for item in items:
            total_price = item.get_total_price()
            html += f'<tr>'
            html += f'<td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{item.variant}</td>'
            html += f'<td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{item.quantity}</td>'
            html += f'<td style="padding: 8px; text-align: right; border-bottom: 1px solid #e5e7eb;">{item.variant.price:.2f} ₽</td>'
            html += f'<td style="padding: 8px; text-align: right; border-bottom: 1px solid #e5e7eb; font-weight: bold;">{total_price:.2f} ₽</td>'
            html += f'</tr>'
        
        html += '</table></div>'
        return format_html(html)
    get_cart_details.short_description = 'Детали корзины'
    
    def status_badge(self, obj):
        """Отобразить статус с цветовой индикацией"""
        badges = {
            'active': ('#10b981', '✓ Активна'),
            'completed': ('#3b82f6', '✓ Завершена'),
            'abandoned': ('#ef4444', '✗ Заброшена'),
        }
        color, text = badges.get(obj.status, ('#9ca3af', obj.status))
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; display: inline-block;">{}</span>',
            color,
            text
        )
    status_badge.short_description = 'Статус'
    
    # Действия
    def mark_as_completed(self, request, queryset):
        """Отметить корзины как завершенные"""
        count = queryset.update(status='completed')
        self.message_user(request, f'Отмечено {count} корзин(а) как завершенные')
    mark_as_completed.short_description = 'Отметить как завершенные'
    
    def mark_as_abandoned(self, request, queryset):
        """Отметить корзины как заброшенные"""
        count = queryset.update(status='abandoned')
        self.message_user(request, f'Отмечено {count} корзин(а) как заброшенные')
    mark_as_abandoned.short_description = 'Отметить как заброшенные'
    
    def clear_carts(self, request, queryset):
        """Очистить выбранные корзины"""
        count = 0
        for cart in queryset:
            cart.items.all().delete()
            count += 1
        self.message_user(request, f'Очищено {count} корзин(а)')
    clear_carts.short_description = 'Очистить корзины'
    
    # Дополнительные настройки
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    def has_delete_permission(self, request, obj=None):
        """Разрешить удаление только суперпользователям"""
        return request.user.is_superuser
    
    class Media:
        css = {
            'all': ('admin/css/cart_admin.css',)
        }


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Админка для элементов корзины"""
    
    list_display = [
        'id',
        'cart',
        'get_variant_name',
        'get_variant_attributes',
        'quantity',
        'get_variant_price',
        'get_total_price',
        'get_variant_stock_status',
        'added_at'
    ]
    
    list_filter = [
        'added_at',
        'cart__status',
        ('cart__user', admin.RelatedOnlyFieldListFilter)
    ]
    
    search_fields = [
        'cart__user__username',
        'cart__user__email',
        'cart__session_key',
        'variant__product__name',
        'variant__sku'
    ]
    
    readonly_fields = [
        'cart',
        'variant',
        'quantity',
        'added_at',
        'get_total_price',
        'get_variant_details'
    ]
    
    fieldsets = (
        ('Корзина', {
            'fields': ('cart',)
        }),
        ('Товар', {
            'fields': ('variant', 'get_variant_details')
        }),
        ('Количество', {
            'fields': ('quantity', 'get_total_price')
        }),
        ('Даты', {
            'fields': ('added_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_variant_name(self, obj):
        """Отобразить название товара"""
        return obj.variant.product.name
    get_variant_name.short_description = 'Товар'
    get_variant_name.admin_order_field = 'variant__product__name'
    
    def get_variant_attributes(self, obj):
        """Отобразить атрибуты варианта"""
        attrs = obj.variant.attributes
        if not attrs:
            return '—'
        return ', '.join([f"{k}: {v}" for k, v in attrs.items()])
    get_variant_attributes.short_description = 'Атрибуты'
    
    def get_variant_price(self, obj):
        """Отобразить цену варианта"""
        return f"{obj.variant.price:.2f} ₽"
    get_variant_price.short_description = 'Цена за ед.'
    get_variant_price.admin_order_field = 'variant__price'
    
    def get_total_price(self, obj):
        total = obj.get_total_price()
        formatted = f"{total:.2f}"
        return format_html('<strong>{} ₽</strong>', formatted)
    get_total_price.short_description = 'Итого'
    
    def get_variant_stock_status(self, obj):
        """Отобразить статус остатка"""
        stock = obj.variant.stock
        quantity = obj.quantity
        
        if stock == 0:
            return format_html('<span style="color: red; font-weight: bold;">Нет в наличии</span>')
        elif quantity > stock:
            return format_html('<span style="color: orange; font-weight: bold;">⚠️ Недостаточно</span>')
        elif stock < 10:
            return format_html('<span style="color: orange;">Низкий остаток ({})</span>', stock)
        else:
            return format_html('<span style="color: green;">✓ В наличии ({})</span>', stock)
    get_variant_stock_status.short_description = 'Остаток'
    
    def get_variant_details(self, obj):
        """Отобразить детали варианта"""
        variant = obj.variant
        old_price_str = f"{variant.old_price:.2f} ₽" if variant.old_price else "—"
        html = f"""
        <div style="padding: 10px; background-color: #f9fafb; border-radius: 4px;">
            <p><strong>Артикул:</strong> {variant.sku or '—'}</p>
            <p><strong>Цена:</strong> {variant.price:.2f} ₽</p>
            <p><strong>Старая цена:</strong> {old_price_str}</p>
            <p><strong>Остаток:</strong> {variant.stock} шт.</p>
            <p><strong>Активен:</strong> {'✓ Да' if variant.is_active else '✗ Нет'}</p>
            <p><strong>Атрибуты:</strong></p>
            <ul style="margin-left: 20px;">
        """
        
        for key, value in variant.attributes.items():
            html += f'<li><strong>{key}:</strong> {value}</li>'
        
        html += '</ul></div>'
        return format_html(html)
    get_variant_details.short_description = 'Детали варианта'
    
    # Дополнительные настройки
    date_hierarchy = 'added_at'
    list_per_page = 50
    ordering = ['-added_at']
    
    def has_delete_permission(self, request, obj=None):
        """Разрешить удаление только суперпользователям"""
        return request.user.is_superuser