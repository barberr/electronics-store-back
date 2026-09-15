import uuid
from django.conf import settings
from django.db import migrations, models
from django.db.models.functions import Lower
import django.db.models.deletion


def check_email_duplicates(apps, schema_editor):
    users = apps.get_model('authentication', 'CustomUser')
    duplicates = (users.objects.using(schema_editor.connection.alias)
        .exclude(email='').annotate(identity=Lower('email')).values('identity')
        .annotate(count=models.Count('pk')).filter(count__gt=1))
    if duplicates.exists():
        raise RuntimeError('Duplicate customer emails (case-insensitive). Resolve duplicates before applying authentication migration; no accounts were merged or deleted.')


class Migration(migrations.Migration):
    dependencies = [('authentication', '0002_customuser_email_verification_fields')]
    operations = [
        migrations.RunPython(check_email_duplicates, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='customuser',
            constraint=models.UniqueConstraint(Lower('email'), condition=~models.Q(email=''), name='customer_email_ci_unique'),
        ),
        migrations.CreateModel(
            name='CustomerSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('revoked', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer_sessions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
