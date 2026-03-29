from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0016_alter_productimage_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='productimage',
            name='color_value',
            field=models.CharField(
                blank=True,
                help_text='Например: Black. Оставьте пустым, если медиа подходит для всех цветов.',
                max_length=100,
                verbose_name='Цвет варианта',
            ),
        ),
    ]
