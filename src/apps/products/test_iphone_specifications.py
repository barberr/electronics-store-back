from importlib import import_module
from io import StringIO
from unittest.mock import patch

from django.apps import apps
from django.core.management import call_command
from django.test import TestCase

from .admin import ProductAdminForm
from .models import Attribute, Category, Product
from .serializers import ProductSerializer


class IphoneSpecificationsTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='iPhone', slug='iphone')
        self.legacy = {
            'year': 2025, 'chip': {'name': 'A19'},
            'display': {'size_inches': 6.3, 'promotion': False},
            'body': {'weight_g': 0}, 'magsafe': True,
            'custom': {'keep': 'unchanged'},
        }
        self.product = Product.objects.create(
            name='Custom iPhone', slug='iphone-test', category=self.category,
            specifications=self.legacy, description='Keep description',
        )

    def test_migration_normalizes_existing_data_and_is_idempotent(self):
        migration = import_module('apps.products.migrations.0019_normalize_iphone_specifications')
        migration.normalize_iphones(apps, None)
        self.product.refresh_from_db()
        specs = self.product.specifications
        self.assertEqual(specs['processor'], 'A19')
        self.assertEqual(specs['screen-size'], 6.3)
        self.assertEqual(specs['promotion'], 'Нет')
        self.assertEqual(specs['weight'], 0)
        self.assertEqual(specs['magsafe'], 'Да')
        self.assertEqual(specs['custom'], {'keep': 'unchanged'})
        self.assertNotIn('chip', specs)
        self.assertEqual(self.product.description, 'Keep description')
        migration.normalize_iphones(apps, None)
        self.product.refresh_from_db()
        self.assertEqual(self.product.specifications, specs)
        data = ProductSerializer(self.product).data['specifications']
        self.assertEqual(data[0]['slug'], 'release-year')
        screen = next(row for row in data if row['slug'] == 'screen-size')
        self.assertEqual(screen['name'], 'Диагональ экрана')
        self.assertEqual(screen['group_name'], 'Экран')
        self.assertEqual(screen['unit'], 'дюйм')

    def test_normalization_preserves_conflicts_and_unknown_nested_fields(self):
        from .iphone_specifications_v1 import normalize_specifications
        source = {'year': 2025, 'release-year': 2024, 'chip': {'name': 'A19', 'extra': 1}}
        result = normalize_specifications(source)
        self.assertEqual(result['release-year'], 2024)
        self.assertEqual(result['year'], 2025)
        self.assertEqual(result['processor'], 'A19')
        self.assertEqual(result['chip'], {'extra': 1})
        self.assertEqual(source['chip'], {'name': 'A19', 'extra': 1})

    def test_import_produces_registered_flat_specs(self):
        from .management.commands.import_iphones import IPHONES
        with patch('apps.products.management.commands.import_iphones.IPHONES', IPHONES[:1]):
            call_command('import_iphones', stdout=StringIO())
        product = Product.objects.get(slug=IPHONES[0]['slug'])
        metadata = set(product.category.attributes.filter(applies_to='product').values_list('slug', flat=True))
        self.assertTrue(set(product.specifications) <= metadata)
        self.assertTrue(all(not isinstance(value, (dict, list, bool)) for value in product.specifications.values()))
        self.assertEqual(product.specifications['release-year'], 2019)

    def test_admin_preserves_unregistered_specifications(self):
        attribute = Attribute.objects.create(name='Процессор', slug='processor')
        self.category.attributes.add(attribute)
        form = ProductAdminForm(instance=self.product)
        form.cleaned_data = {'spec__processor': 'A19'}
        cleaned = form.clean()
        self.assertEqual(cleaned['specifications']['custom'], {'keep': 'unchanged'})
        self.assertEqual(cleaned['specifications']['processor'], 'A19')
