from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Cart(models.Model):
    """Корзина покупок"""
    
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('completed', 'Завершена'),
        ('abandoned', 'Заброшена'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )
    
    session_key = models.CharField(
        max_length=40,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Ключ сессии'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Статус'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлена')
    
    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.user:
            return f"Корзина пользователя {self.user.username}"
        return f"Корзина сессии {self.session_key}"
    
    def get_total_items(self):
        """Общее количество товаров в корзине"""
        return sum(item.quantity for item in self.items.all())
    
    def get_total_price(self):
        """Общая стоимость товаров в корзине"""
        return sum(item.get_total_price() for item in self.items.all())


class CartItem(models.Model):
    """Элемент корзины"""
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Корзина'
    )
    
    # Ссылка на модель из приложения products
    variant = models.ForeignKey(
        'products.ProductVariant',  # ← Исправлено: products вместо catalog
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='Вариант товара'
    )
    
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Количество'
    )
    
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')
    
    class Meta:
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Элементы корзины'
        unique_together = ['cart', 'variant']
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.variant} × {self.quantity}"
    
    def get_total_price(self):
        """Общая стоимость этого элемента"""
        return self.variant.price * self.quantity
    
    def clean(self):
        """Валидация перед сохранением"""
        if self.quantity > self.variant.stock:
            raise ValueError(f"Недостаточно товара на складе. Доступно: {self.variant.stock}")