from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from pathlib import Path
import tempfile

from .admin import ProductAdminForm, ProductImageAdminForm, ProductVariantAdminForm
from .models import Attribute, Brand, Category, Product, ProductImage, ProductVariant


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


class PopularProductsAPITests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Смартфоны',
            slug='smartphones',
        )

        self.first_product = Product.objects.create(
            name='iPhone 15 Pro',
            slug='iphone-15-pro',
            category=self.category,
            is_active=True,
            is_popular=True,
            popular_order=20,
        )
        self.second_product = Product.objects.create(
            name='iPhone 15',
            slug='iphone-15',
            category=self.category,
            is_active=True,
            is_popular=True,
            popular_order=10,
        )
        self.non_popular_product = Product.objects.create(
            name='iPhone SE',
            slug='iphone-se',
            category=self.category,
            is_active=True,
            is_popular=False,
            popular_order=1,
        )

    def test_popular_products_are_sorted_by_popular_order(self):
        response = self.client.get('/api/v1/products/popular/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [product['slug'] for product in response.data],
            [self.second_product.slug, self.first_product.slug],
        )


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
                'popular_order': '0',
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

    def test_product_image_form_builds_color_choices_from_category_attribute(self):
        color = Attribute.objects.create(
            name='Цвет',
            slug='color',
            applies_to='variant',
            type='enum',
            values=['Black', 'White'],
        )
        self.category.attributes.add(color)
        product = Product.objects.create(
            name='iPhone 15 Pro',
            slug='iphone-15-pro',
            category=self.category,
            brand=self.brand,
        )

        form = ProductImageAdminForm(category=self.category, instance=ProductImage(product=product))

        self.assertEqual(
            list(form.fields['color_value'].choices),
            [('', '---------'), ('Black', 'Black'), ('White', 'White')],
        )

    def test_product_image_form_keeps_existing_color_value_if_missing_in_attribute(self):
        color = Attribute.objects.create(
            name='Цвет',
            slug='color',
            applies_to='variant',
            type='enum',
            values=['White'],
        )
        self.category.attributes.add(color)
        product = Product.objects.create(
            name='iPhone 15 Pro',
            slug='iphone-15-pro',
            category=self.category,
            brand=self.brand,
        )

        form = ProductImageAdminForm(
            category=self.category,
            instance=ProductImage(product=product, color_value='Black'),
        )

        self.assertEqual(
            list(form.fields['color_value'].choices),
            [('', '---------'), ('White', 'White'), ('Black', 'Black')],
        )

    def test_product_image_model_validates_color_value_against_color_attribute(self):
        color = Attribute.objects.create(
            name='Цвет',
            slug='color',
            applies_to='variant',
            type='enum',
            values=['Black', 'White'],
        )
        self.category.attributes.add(color)
        product = Product.objects.create(
            name='iPhone 15 Pro',
            slug='iphone-15-pro',
            category=self.category,
            brand=self.brand,
        )

        media = ProductImage(
            product=product,
            image=SimpleUploadedFile('demo.jpg', b'fake-image-content', content_type='image/jpeg'),
            color_value='Gold',
        )

        with self.assertRaisesMessage(ValidationError, 'Выберите одно из значений атрибута color'):
            media.full_clean()

    def test_product_image_model_requires_color_attribute_when_color_value_is_set(self):
        product = Product.objects.create(
            name='iPhone 15 Pro',
            slug='iphone-15-pro',
            category=self.category,
            brand=self.brand,
        )

        media = ProductImage(
            product=product,
            image=SimpleUploadedFile('demo.jpg', b'fake-image-content', content_type='image/jpeg'),
            color_value='Black',
        )

        with self.assertRaisesMessage(ValidationError, 'Для категории товара не настроен variant-атрибут color'):
            media.full_clean()


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
        self.color = Attribute.objects.create(
            name='Цвет',
            slug='color',
            applies_to='variant',
            type='enum',
            values=['Black', 'White'],
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
        self.category.attributes.add(self.screen_size, self.storage, self.color)

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
            attributes={'storage': '256GB', 'color': 'Black'},
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
        self.assertEqual(response.data['variants'][0]['attributes']['storage'], '256GB')
        self.assertEqual(response.data['variants'][0]['attributes']['color'], 'Black')
        attribute_values = {item['slug']: item['value'] for item in response.data['variants'][0]['attribute_values']}
        self.assertEqual(attribute_values['storage'], '256GB')
        self.assertEqual(attribute_values['color'], 'Black')

    def test_variant_media_includes_common_and_color_specific_assets(self):
        ProductImage.objects.create(
            product=self.product,
            image=SimpleUploadedFile('common.jpg', b'fake-image-content', content_type='image/jpeg'),
            alt_text='common',
            order=0,
        )
        ProductImage.objects.create(
            product=self.product,
            image=SimpleUploadedFile('black.mp4', b'fake-mp4-content', content_type='video/mp4'),
            alt_text='black',
            color_value='Black',
            order=1,
        )
        ProductImage.objects.create(
            product=self.product,
            image=SimpleUploadedFile('white.jpg', b'fake-image-content', content_type='image/jpeg'),
            alt_text='white',
            color_value='White',
            order=2,
        )

        response = self.client.get(f'/api/v1/products/{self.product.slug}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        media = response.data['variants'][0]['media']
        self.assertEqual(len(media), 2)
        self.assertEqual(media[0]['alt_text'], 'common')
        self.assertEqual(media[1]['alt_text'], 'black')
        self.assertEqual(media[1]['media_type'], 'video')

    def test_variant_without_color_receives_only_common_media(self):
        ProductImage.objects.create(
            product=self.product,
            image=SimpleUploadedFile('common.jpg', b'fake-image-content', content_type='image/jpeg'),
            alt_text='common',
            order=0,
        )
        ProductImage.objects.create(
            product=self.product,
            image=SimpleUploadedFile('black.jpg', b'fake-image-content', content_type='image/jpeg'),
            alt_text='black',
            color_value='Black',
            order=1,
        )
        ProductVariant.objects.create(
            product=self.product,
            sku='APL-IP15PRO-128',
            attributes={'storage': '128GB'},
            price='899.00',
            stock=3,
            is_active=True,
        )

        response = self.client.get(f'/api/v1/products/{self.product.slug}/')

        variant = next(item for item in response.data['variants'] if item['sku'] == 'APL-IP15PRO-128')
        self.assertEqual(len(variant['media']), 1)
        self.assertEqual(variant['media'][0]['alt_text'], 'common')


class ProductMediaTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Смартфоны',
            slug='smartphones',
        )
        self.product = Product.objects.create(
            name='iPhone 15 Pro',
            slug='iphone-15-pro',
            category=self.category,
        )

    def test_product_media_accepts_mp4(self):
        media = ProductImage(
            product=self.product,
            image=SimpleUploadedFile('demo.mp4', b'fake-mp4-content', content_type='video/mp4'),
        )

        media.full_clean()

    def test_product_media_rejects_unsupported_extension(self):
        media = ProductImage(
            product=self.product,
            image=SimpleUploadedFile('demo.mov', b'fake-video-content', content_type='video/quicktime'),
        )

        with self.assertRaisesMessage(ValidationError, 'Поддерживаются изображения'):
            media.full_clean()

    def test_product_detail_returns_media_type_for_videos(self):
        ProductImage.objects.create(
            product=self.product,
            image=SimpleUploadedFile('demo.mp4', b'fake-mp4-content', content_type='video/mp4'),
            alt_text='promo',
            color_value='',
            order=0,
        )

        response = self.client.get(f'/api/v1/products/{self.product.slug}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['images'][0]['media_type'], 'video')
        self.assertTrue(response.data['images'][0]['image'].endswith('.mp4'))


class ProductImportCommandTests(TestCase):
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_import_products_xlsx_creates_products_variants_and_media_without_duplicates(self):
        try:
            from openpyxl import Workbook
        except ImportError:
            self.skipTest('openpyxl is not installed')

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            workbook = Workbook()
            worksheet = workbook.active
            worksheet.append([
                'Серия', 'Модель_из_файла', 'ОЗУ', 'Диагональ', 'Цвет_вариант', 'Цветы_всего',
                'Связь', 'Процессор', 'Год', 'Разъём', 'Комплект', 'MagSafe', 'Корпус',
                'gallery_id', 'Фото_1', 'Фото_2', 'Фото_3',
            ])
            worksheet.append([
                '13', '13', '128GB', '6.1"', '(PRODUCT)RED',
                '(PRODUCT)RED; Starlight; Midnight; Blue; Pink; Green',
                '5G, Wi-Fi, Bluetooth', 'A15 Bionic', '2021', 'Lightning',
                'iPhone, кабель USB-C to Lightning, документация', 'Да',
                'Алюминий, стеклянная задняя панель', '13',
                '13_01.webp', '13_02.webp', '13_03.webp',
            ])
            worksheet.append([
                '13', '13', '256GB', '6.1"', 'Starlight',
                '(PRODUCT)RED; Starlight; Midnight; Blue; Pink; Green',
                '5G, Wi-Fi, Bluetooth', 'A15 Bionic', '2021', 'Lightning',
                'iPhone, кабель USB-C to Lightning, документация', 'Да',
                'Алюминий, стеклянная задняя панель', '13',
                '13_01.webp', '13_02.webp', '13_03.webp',
            ])

            xlsx_path = temp_path / 'products.xlsx'
            workbook.save(xlsx_path)

            for filename in ('13_01.webp', '13_02.webp', '13_03.webp'):
                (temp_path / filename).write_bytes(b'fake-image-content')

            command_kwargs = {
                'category_slug': 'smartphones',
                'category_name': 'Смартфоны',
                'brand_slug': 'apple',
                'brand_name': 'Apple',
                'media_dir': str(temp_path),
                'product_name_template': '{brand} iPhone {model}',
                'default_price': '799.00',
                'default_stock': 7,
            }

            call_command('import_products_xlsx', str(xlsx_path), **command_kwargs)
            call_command('import_products_xlsx', str(xlsx_path), **command_kwargs)

        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(ProductVariant.objects.count(), 2)
        self.assertEqual(ProductImage.objects.count(), 3)

        product = Product.objects.get()
        self.assertEqual(product.name, 'Apple iPhone 13')
        self.assertEqual(product.specifications['screen-size'], '6.1"')
        self.assertEqual(product.specifications['processor'], 'A15 Bionic')
        self.assertEqual(product.specifications['release-year'], '2021')
        self.assertEqual(product.specifications['magsafe'], 'Да')

        variants = {
            (variant.attributes.get('storage'), variant.attributes.get('color')): variant
            for variant in ProductVariant.objects.filter(product=product)
        }
        self.assertIn(('128GB', '(PRODUCT)RED'), variants)
        self.assertIn(('256GB', 'Starlight'), variants)
        self.assertTrue(all(str(variant.price) == '799.00' for variant in variants.values()))
        self.assertTrue(all(variant.stock == 7 for variant in variants.values()))

        color_attribute = Attribute.objects.get(slug='color')
        self.assertEqual(color_attribute.applies_to, 'variant')
        self.assertEqual(
            color_attribute.values,
            ['(PRODUCT)RED', 'Blue', 'Green', 'Midnight', 'Pink', 'Starlight'],
        )

        storage_attribute = Attribute.objects.get(slug='storage')
        self.assertEqual(storage_attribute.values, ['128GB', '256GB'])

        category = Category.objects.get(slug='smartphones')
        self.assertEqual(category.attributes.count(), 10)
        self.assertEqual(
            list(product.images.order_by('order').values_list('color_value', flat=True)),
            ['', '', ''],
        )
