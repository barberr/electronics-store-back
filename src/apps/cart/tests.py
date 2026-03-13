from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.products.models import Category, Product, ProductVariant


class GuestCartViewSetTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Phones',
            slug='phones',
        )
        self.product = Product.objects.create(
            name='Phone X',
            slug='phone-x',
            category=self.category,
            is_active=True,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku='PHONE-X-128',
            attributes={'storage': '128GB'},
            price=Decimal('999.99'),
            is_active=True,
            stock=10,
        )
        self.cart_add_url = reverse('cart-add-item')
        self.cart_list_url = reverse('cart-list')

    def test_guest_add_item_increases_total_items_and_quantity(self):
        first_response = self.client.post(
            self.cart_add_url,
            {'variant_id': self.variant.id, 'quantity': 2},
            format='json',
        )

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(first_response.data['total_items'], 2)
        self.assertEqual(len(first_response.data['items']), 1)
        self.assertEqual(first_response.data['items'][0]['quantity'], 2)
        self.assertEqual(first_response.data['items'][0]['total_price'], '1999.98')

        second_response = self.client.post(
            self.cart_add_url,
            {'variant_id': self.variant.id, 'quantity': 1},
            format='json',
        )

        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.data['total_items'], 3)
        self.assertEqual(len(second_response.data['items']), 1)
        self.assertEqual(second_response.data['items'][0]['quantity'], 3)
        self.assertEqual(second_response.data['total_price'], '2999.97')

        list_response = self.client.get(self.cart_list_url)

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data['total_items'], 3)
        self.assertEqual(len(list_response.data['items']), 1)
        self.assertEqual(list_response.data['items'][0]['quantity'], 3)
