from django.db import migrations, models

import apps.products.models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0015_product_specifications_attribute_metadata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productimage',
            name='image',
            field=models.FileField(
                upload_to='products/images/%Y/%m/%d/',
                validators=[apps.products.models.validate_product_media_file],
                verbose_name='Медиа',
            ),
        ),
        migrations.AlterModelOptions(
            name='productimage',
            options={
                'ordering': ['order'],
                'verbose_name': 'Медиафайл',
                'verbose_name_plural': 'Медиафайлы',
            },
        ),
    ]
