from rest_framework import status
from rest_framework.test import APITestCase

from .models import Brand, Category, Product, ProductVariant


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

        self.matching_product = Product.objects.create(
            name='iPhone 15 Pro',
            slug='iphone-15-pro',
            brand=self.brand,
            category=self.category,
            short_description='Флагманский смартфон Apple',
            description='Смартфон с титановым корпусом',
            is_active=True,
        )
        ProductVariant.objects.create(
            product=self.matching_product,
            sku='APL-IP15PRO-256',
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

    def test_search_requires_non_empty_query(self):
        response = self.client.get('/api/v1/products/search/', {'q': '   '})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Query parameter "q" is required.')

    def test_search_excludes_inactive_products(self):
        response = self.client.get('/api/v1/products/search/', {'q': 'неактивный'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['results'], [])
