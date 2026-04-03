from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0017_productimage_color_value'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='popular_order',
            field=models.PositiveIntegerField(default=0, verbose_name='Порядок в популярных'),
        ),
    ]
