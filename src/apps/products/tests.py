from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .admin import ProductAdminForm, ProductVariantAdminForm
from .models import Attribute, Brand, Category, Product, ProductVariant


class ProductSearchAPITests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Смартфоны',
            slug='smartphones',
        )
        self.other_category = Category.objects.create(
            name='Ноутбуки',
            slug='laptops',
        )
        self.brand = Brand.objects.create(
            name='Apple',
            slug='apple',
        )
        self.screen_size = Attribute.objects.create(
            name='Диагональ экрана',
            slug='screen-size',
            applies_to='product',
            type='number',
        )
        self.storage = Attribute.objects.create(
            name='Память',
            slug='storage',
            applies_to='variant',
            type='enum',
            values=['128GB', '256GB'],
        )
        self.category.attributes.add(self.screen_size, self.storage)

        self.matching_product = Product.objects.create(
            name='iPhone 15 Pro',
            slug='iphone-15-pro',
            brand=self.brand,
            category=self.category,
            short_description='Флагманский смартфон Apple',
            description='Смартфон с титановым корпусом',
            specifications={'screen-size': '6.1'},
            is_active=True,
        )
        ProductVariant.objects.create(
            product=self.matching_product,
            sku='APL-IP15PRO-256',
            attributes={'storage': '256GB'},
            price='999.00',
            stock=5,
            is_active=True,
        )

        self.second_matching_product = Product.objects.create(
            name='MacBook Air',
            slug='macbook-air',
            brand=self.brand,
            category=self.other_category,
            short_description='Ноутбук Apple',
            description='Легкий ноутбук для работы',
            specifications={'screen-size': '13.6'},
            is_active=True,
        )

        self.inactive_product = Product.objects.create(
            name='iPhone 15',
            slug='iphone-15',
            brand=self.brand,
            category=self.category,
            short_description='Не должен попасть в поиск',
            description='Неактивный товар',
            is_active=False,
        )

    def test_search_returns_products_matching_query(self):
        response = self.client.get('/api/v1/products/search/', {'q': 'iphone'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['slug'], self.matching_product.slug)

    def test_search_matches_related_brand_and_variant_sku(self):
        response = self.client.get('/api/v1/products/search/', {'q': 'APL-IP15PRO'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['slug'], self.matching_product.slug)

    def test_search_matches_product_and_variant_characteristics(self):
        response = self.client.get('/api/v1/products/search/', {'q': '256GB'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['slug'], self.matching_product.slug)

    def test_search_requires_non_empty_query(self):
        response = self.client.get('/api/v1/products/search/', {'q': '   '})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Query parameter "q" is required.')

    def test_search_excludes_inactive_products(self):
        response = self.client.get('/api/v1/products/search/', {'q': 'неактивный'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['results'], [])

    def test_list_filters_by_product_specification(self):
        response = self.client.get('/api/v1/products/', {'spec__screen-size': '6.1'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['slug'], self.matching_product.slug)

    def test_list_filters_by_variant_attribute(self):
        response = self.client.get('/api/v1/products/', {'attr__storage': '256GB'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['slug'], self.matching_product.slug)


class BrandDetailAPITests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Смартфоны',
            slug='smartphones',
        )
        self.brand = Brand.objects.create(
            name='Apple',
            slug='apple',
        )

        self.active_product = Product.objects.create(
            name='iPhone 15 Pro',
            slug='iphone-15-pro',
            brand=self.brand,
            category=self.category,
            is_active=True,
        )
        ProductVariant.objects.create(
            product=self.active_product,
            sku='APL-IP15PRO-256',
            price='999.00',
            stock=5,
            is_active=True,
        )

        Product.objects.create(
            name='iPhone 15',
            slug='iphone-15',
            brand=self.brand,
            category=self.category,
            is_active=False,
        )

    def test_brand_detail_includes_only_active_brand_products(self):
        response = self.client.get(f'/api/v1/brands/{self.brand.slug}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slug'], self.brand.slug)
        self.assertIn('products', response.data)
        self.assertEqual(len(response.data['products']), 1)
        self.assertEqual(response.data['products'][0]['slug'], self.active_product.slug)


class ProductAdminFormTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Смартфоны',
            slug='smartphones',
        )
        self.brand = Brand.objects.create(
            name='Apple',
            slug='apple',
        )

    def test_product_form_builds_category_specific_fields_and_saves_specifications(self):
        screen_size = Attribute.objects.create(
            name='Диагональ экрана',
            slug='screen-size',
            applies_to='product',
            type='number',
            is_required=True,
        )
        color = Attribute.objects.create(
            name='Цвет',
            slug='color',
            applies_to='variant',
            type='enum',
            values=['Black', 'White'],
        )
        self.category.attributes.add(screen_size, color)

        form = ProductAdminForm(
            data={
                'name': 'iPhone 15 Pro',
                'slug': 'iphone-15-pro',
                'category': str(self.category.pk),
                'brand': str(self.brand.pk),
                'short_description': '',
                'description': '',
                'delivery_text': '',
                'seo_title': '',
                'seo_description': '',
                'warranty_months': '12',
                'is_active': 'on',
                'is_preorder': '',
                'is_popular': '',
                'spec__screen-size': '6.1',
            }
        )

        self.assertIn('spec__screen-size', form.fields)
        self.assertNotIn('spec__color', form.fields)
        self.assertTrue(form.is_valid(), form.errors)

        product = form.save()

        self.assertEqual(product.specifications, {'screen-size': '6.1'})

    def test_variant_form_builds_category_specific_fields_and_saves_attributes(self):
        storage = Attribute.objects.create(
            name='Память',
            slug='storage',
            applies_to='variant',
            type='enum',
            values=['128GB', '256GB'],
            is_required=True,
        )
        self.category.attributes.add(storage)

        product = Product.objects.create(
            name='iPhone 15 Pro',
            slug='iphone-15-pro',
            category=self.category,
            brand=self.brand,
        )

        form = ProductVariantAdminForm(
            category=self.category,
            data={
                'product': str(product.pk),
                'sku': 'APL-IP15PRO-256',
                'price': '999.00',
                'old_price': '',
                'is_active': 'on',
                'stock': '5',
                'attr__storage': '256GB',
            },
        )

        self.assertIn('attr__storage', form.fields)
        self.assertTrue(form.is_valid(), form.errors)

        variant = form.save(commit=False)
        variant.product = product
        variant.save()

        self.assertEqual(variant.attributes, {'storage': '256GB'})


class ProductCharacteristicsAPITests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Смартфоны',
            slug='smartphones',
        )
        self.brand = Brand.objects.create(
            name='Apple',
            slug='apple',
        )
        self.screen_size = Attribute.objects.create(
            name='Диагональ экрана',
            slug='screen-size',
            applies_to='product',
            type='number',
            unit='дюйм',
        )
        self.storage = Attribute.objects.create(
            name='Память',
            slug='storage',
            applies_to='variant',
            type='enum',
            values=['128GB', '256GB'],
        )
        self.category.attributes.add(self.screen_size, self.storage)

        self.product = Product.objects.create(
            name='iPhone 15 Pro',
            slug='iphone-15-pro',
            brand=self.brand,
            category=self.category,
            specifications={'screen-size': '6.1'},
            is_active=True,
        )
        ProductVariant.objects.create(
            product=self.product,
            sku='APL-IP15PRO-256',
            attributes={'storage': '256GB'},
            price='999.00',
            stock=5,
            is_active=True,
        )

    def test_product_detail_returns_structured_specifications_and_variant_attributes(self):
        response = self.client.get(f'/api/v1/products/{self.product.slug}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['specifications_map'], {'screen-size': '6.1'})
        self.assertEqual(response.data['specifications'][0]['slug'], 'screen-size')
        self.assertEqual(response.data['specifications'][0]['unit'], 'дюйм')
        self.assertEqual(response.data['specifications'][0]['value'], '6.1')
        self.assertEqual(response.data['variants'][0]['attributes'], {'storage': '256GB'})
        self.assertEqual(response.data['variants'][0]['attribute_values'][0]['slug'], 'storage')
        self.assertEqual(response.data['variants'][0]['attribute_values'][0]['value'], '256GB')
