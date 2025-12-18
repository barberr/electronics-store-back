from django.db import models
from django.core.validators import MinValueValidator

class Category(models.Model):
    name = models.CharField("Название", max_length=100, unique=True)
    slug = models.SlugField("Слаг", max_length=100, unique=True)
    description = models.TextField("Описание", blank=True)
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField("Название", max_length=200)
    slug = models.SlugField("Слаг", max_length=200, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    description = models.TextField("Описание", blank=True)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.PositiveIntegerField("Остаток", default=0)
    is_available = models.BooleanField("Доступен", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at']
    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("Изображение", upload_to="products/images/%Y/%m/%d/")
    is_main = models.BooleanField("Главное", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"
    def __str__(self):
        return f"{self.product} - {self.image}"