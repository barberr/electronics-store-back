from django.db import migrations

from apps.products.iphone_specifications_v1 import normalize_specifications, register_attributes


def normalize_iphones(apps, schema_editor):
    using = schema_editor.connection.alias if schema_editor else 'default'
    Category = apps.get_model('products', 'Category')
    Attribute = apps.get_model('products', 'Attribute')
    Product = apps.get_model('products', 'Product')
    category = Category.objects.using(using).filter(slug='iphone').first()
    if category is None:
        return
    register_attributes(Attribute, category, using)
    for product in Product.objects.using(using).filter(category_id=category.pk).iterator():
        normalized = normalize_specifications(product.specifications)
        if normalized != product.specifications:
            Product.objects.using(using).filter(pk=product.pk).update(specifications=normalized)


class Migration(migrations.Migration):
    dependencies = [('products', '0018_product_popular_order')]
    operations = [migrations.RunPython(normalize_iphones)]
