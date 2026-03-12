from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='email_verification_pin',
            field=models.CharField(blank=True, max_length=6),
        ),
        migrations.AddField(
            model_name='customuser',
            name='email_verification_pin_expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='is_email_verified',
            field=models.BooleanField(default=False),
        ),
    ]
