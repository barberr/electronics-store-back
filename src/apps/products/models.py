from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

class Brand(models.Model):
    name = models.CharField("Название", max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to="brands/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Брэнд"
        verbose_name_plural = "Брэнды"

    def __str__(self):
        return self.name

class Attribute(models.Model):
    TYPE_CHOICES = [
        ('string', 'Строка'),
        ('number', 'Число'),
        ('enum', 'Список'),
    ]

    name = models.CharField("Название", max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    type = models.CharField("Тип", max_length=20, choices=TYPE_CHOICES, default='string')
    values = models.JSONField("Возможные значения", blank=True, null=True, help_text="Для enum: [\"red\", \"blue\"]")

    class Meta:
        verbose_name = "Атрибут"
        verbose_name_plural = "Атрибуты"

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField("Название", max_length=100, unique=True)
    slug = models.SlugField("Слаг", max_length=100, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Родительская категория"
    )
    description = models.TextField("Описание", blank=True)
    image = models.ImageField("Изображение", upload_to="categories/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    attributes = models.ManyToManyField(Attribute, blank=True, related_name='categories')

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField("Название", max_length=200)
    slug = models.SlugField("Слаг", max_length=200, unique=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    
    short_description = models.CharField("Краткое описание", max_length=255, blank=True)
    description = models.TextField("Описание", blank=True)
    
    seo_title = models.CharField("SEO заголовок", max_length=150, blank=True)
    seo_description = models.TextField("SEO описание", max_length=300, blank=True)
    
    is_active = models.BooleanField("Активен", default=True)
    is_preorder = models.BooleanField("Предзаказ", default=False)
    delivery_text = models.TextField("Текст доставки", blank=True)
    warranty_months = models.PositiveSmallIntegerField("Гарантия (мес)", default=12)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("Изображение", upload_to="products/images/%Y/%m/%d/")
    alt_text = models.CharField("Alt текст", max_length=255, blank=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"
        ordering = ['order']

    def __str__(self):
        return f"{self.product} - {self.image}"

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField("Артикул", max_length=100, unique=True, blank=True, null=True)
    
    # Пример: {"color": "Red", "storage": "256GB"}
    attributes = models.JSONField("Атрибуты", default=dict, blank=True)
    
    price = models.DecimalField(
        "Цена",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    old_price = models.DecimalField(
        "Старая цена",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True,
        null=True
    )
    is_active = models.BooleanField("Активен", default=True)
    stock = models.PositiveIntegerField("Остаток", default=0)

    class Meta:
        verbose_name = "Вариант товара"
        verbose_name_plural = "Варианты товаров"

    def __str__(self):
        attrs = ', '.join([f"{k}: {v}" for k, v in self.attributes.items()])
        return f"{self.product.name} — {attrs}"


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders"
    )
    contact_phone = models.CharField("Контактный телефон", max_length=20)
    contact_name = models.CharField("Контактное имя", max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Заказ #{self.id} — {self.contact_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    variant = models.ForeignKey('ProductVariant', on_delete=models.PROTECT)  # ← связь с вариантом
    quantity = models.PositiveIntegerField("Количество", default=1)
    price_at_time = models.DecimalField(  # Цена на момент заказа
        "Цена при заказе",
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"{self.variant} × {self.quantity}"