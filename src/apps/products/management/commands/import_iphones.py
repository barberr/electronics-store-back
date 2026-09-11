"""
Импорт каталога Apple iPhone 11 -> актуальная линейка.

Размещение:
    <your_app>/management/commands/import_iphones.py

Запуск:
    python manage.py import_iphones

Повторный запуск безопасен:
- Brand / Category / Attribute / Product обновляются через update_or_create;
- ProductVariant ищется по product + attributes;
- существующие price / old_price / stock / is_active у вариантов НЕ перезаписываются.

ВАЖНО:
Новые варианты создаются с price=0, stock=0, is_active=False, чтобы импорт
характеристик случайно не выставил товар в продажу.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from ...models import Brand, Category, Attribute, Product, ProductVariant
from ...iphone_specifications_v1 import normalize_specifications, register_attributes


def display(
    size,
    resolution,
    ppi,
    *,
    refresh_rate="60 Гц",
    promotion=False,
    always_on=False,
    dynamic_island=False,
    display_type="Super Retina XDR OLED",
):
    return {
        "type": display_type,
        "size_inches": size,
        "resolution": resolution,
        "ppi": ppi,
        "refresh_rate": refresh_rate,
        "promotion": promotion,
        "always_on": always_on,
        "dynamic_island": dynamic_island,
    }


def body(width, height, depth, weight, material):
    return {
        "width_mm": width,
        "height_mm": height,
        "depth_mm": depth,
        "weight_g": weight,
        "material": material,
        "water_resistance": "IP68",
    }


def specs(
    year,
    chip,
    display_data,
    body_data,
    *,
    connector,
    camera_main,
    camera_ultrawide=None,
    camera_telephoto=None,
    camera_front="12 Мп",
    magsafe=True,
    network_5g=True,
    face_id=True,
    apple_intelligence=False,
):
    camera = {
        "main": camera_main,
        "front": camera_front,
    }
    if camera_ultrawide:
        camera["ultrawide"] = camera_ultrawide
    if camera_telephoto:
        camera["telephoto"] = camera_telephoto

    return {
        "year": year,
        "chip": {"name": chip},
        "display": display_data,
        "camera": camera,
        "body": body_data,
        "connector": connector,
        "magsafe": magsafe,
        "5g": network_5g,
        "face_id": face_id,
        "apple_intelligence": apple_intelligence,
    }


IPHONES = [
    # ------------------------------------------------------------------
    # iPhone 11
    # ------------------------------------------------------------------
    {
        "name": "iPhone 11",
        "slug": "iphone-11",
        "storage": ["64GB", "128GB", "256GB"],
        "colors": ["Black", "Green", "Yellow", "Purple", "(PRODUCT)RED", "White"],
        "specifications": specs(
            2019, "A13 Bionic",
            display(
                6.1, "1792 × 828", 326,
                display_type="Liquid Retina HD LCD",
            ),
            body(75.7, 150.9, 8.3, 194, "Алюминий и стекло"),
            connector="Lightning",
            camera_main="12 Мп",
            camera_ultrawide="12 Мп",
            magsafe=False,
            network_5g=False,
        ),
    },
    {
        "name": "iPhone 11 Pro",
        "slug": "iphone-11-pro",
        "storage": ["64GB", "256GB", "512GB"],
        "colors": ["Space Gray", "Silver", "Gold", "Midnight Green"],
        "specifications": specs(
            2019, "A13 Bionic",
            display(5.8, "2436 × 1125", 458),
            body(71.4, 144.0, 8.1, 188, "Нержавеющая сталь и стекло"),
            connector="Lightning",
            camera_main="12 Мп",
            camera_ultrawide="12 Мп",
            camera_telephoto="12 Мп 2x",
            magsafe=False,
            network_5g=False,
        ),
    },
    {
        "name": "iPhone 11 Pro Max",
        "slug": "iphone-11-pro-max",
        "storage": ["64GB", "256GB", "512GB"],
        "colors": ["Space Gray", "Silver", "Gold", "Midnight Green"],
        "specifications": specs(
            2019, "A13 Bionic",
            display(6.5, "2688 × 1242", 458),
            body(77.8, 158.0, 8.1, 226, "Нержавеющая сталь и стекло"),
            connector="Lightning",
            camera_main="12 Мп",
            camera_ultrawide="12 Мп",
            camera_telephoto="12 Мп 2x",
            magsafe=False,
            network_5g=False,
        ),
    },

    # ------------------------------------------------------------------
    # iPhone 12
    # ------------------------------------------------------------------
    {
        "name": "iPhone 12 mini",
        "slug": "iphone-12-mini",
        "storage": ["64GB", "128GB", "256GB"],
        "colors": ["Black", "White", "(PRODUCT)RED", "Green", "Blue", "Purple"],
        "specifications": specs(
            2020, "A14 Bionic",
            display(5.4, "2340 × 1080", 476),
            body(64.2, 131.5, 7.4, 133, "Алюминий и стекло"),
            connector="Lightning",
            camera_main="12 Мп",
            camera_ultrawide="12 Мп",
        ),
    },
    {
        "name": "iPhone 12",
        "slug": "iphone-12",
        "storage": ["64GB", "128GB", "256GB"],
        "colors": ["Black", "White", "(PRODUCT)RED", "Green", "Blue", "Purple"],
        "specifications": specs(
            2020, "A14 Bionic",
            display(6.1, "2532 × 1170", 460),
            body(71.5, 146.7, 7.4, 162, "Алюминий и стекло"),
            connector="Lightning",
            camera_main="12 Мп",
            camera_ultrawide="12 Мп",
        ),
    },
    {
        "name": "iPhone 12 Pro",
        "slug": "iphone-12-pro",
        "storage": ["128GB", "256GB", "512GB"],
        "colors": ["Silver", "Graphite", "Gold", "Pacific Blue"],
        "specifications": specs(
            2020, "A14 Bionic",
            display(6.1, "2532 × 1170", 460),
            body(71.5, 146.7, 7.4, 187, "Нержавеющая сталь и стекло"),
            connector="Lightning",
            camera_main="12 Мп",
            camera_ultrawide="12 Мп",
            camera_telephoto="12 Мп 2x",
        ),
    },
    {
        "name": "iPhone 12 Pro Max",
        "slug": "iphone-12-pro-max",
        "storage": ["128GB", "256GB", "512GB"],
        "colors": ["Silver", "Graphite", "Gold", "Pacific Blue"],
        "specifications": specs(
            2020, "A14 Bionic",
            display(6.7, "2778 × 1284", 458),
            body(78.1, 160.8, 7.4, 226, "Нержавеющая сталь и стекло"),
            connector="Lightning",
            camera_main="12 Мп",
            camera_ultrawide="12 Мп",
            camera_telephoto="12 Мп 2.5x",
        ),
    },

    # ------------------------------------------------------------------
    # iPhone 13
    # ------------------------------------------------------------------
    {
        "name": "iPhone 13 mini",
        "slug": "iphone-13-mini",
        "storage": ["128GB", "256GB", "512GB"],
        "colors": ["(PRODUCT)RED", "Starlight", "Midnight", "Blue", "Pink", "Green"],
        "specifications": specs(
            2021, "A15 Bionic",
            display(5.4, "2340 × 1080", 476),
            body(64.2, 131.5, 7.65, 140, "Алюминий и стекло"),
            connector="Lightning",
            camera_main="12 Мп",
            camera_ultrawide="12 Мп",
        ),
    },
    {
        "name": "iPhone 13",
        "slug": "iphone-13",
        "storage": ["128GB", "256GB", "512GB"],
        "colors": ["(PRODUCT)RED", "Starlight", "Midnight", "Blue", "Pink", "Green"],
        "specifications": specs(
            2021, "A15 Bionic",
            display(6.1, "2532 × 1170", 460),
            body(71.5, 146.7, 7.65, 174, "Алюминий и стекло"),
            connector="Lightning",
            camera_main="12 Мп",
            camera_ultrawide="12 Мп",
        ),
    },
    {
        "name": "iPhone 13 Pro",
        "slug": "iphone-13-pro",
        "storage": ["128GB", "256GB", "512GB", "1TB"],
        "colors": ["Graphite", "Gold", "Silver", "Sierra Blue", "Alpine Green"],
        "specifications": specs(
            2021, "A15 Bionic",
            display(
                6.1, "2532 × 1170", 460,
                refresh_rate="10–120 Гц", promotion=True,
            ),
            body(71.5, 146.7, 7.65, 204, "Нержавеющая сталь и стекло"),
            connector="Lightning",
            camera_main="12 Мп",
            camera_ultrawide="12 Мп",
            camera_telephoto="12 Мп 3x",
        ),
    },
    {
        "name": "iPhone 13 Pro Max",
        "slug": "iphone-13-pro-max",
        "storage": ["128GB", "256GB", "512GB", "1TB"],
        "colors": ["Graphite", "Gold", "Silver", "Sierra Blue", "Alpine Green"],
        "specifications": specs(
            2021, "A15 Bionic",
            display(
                6.7, "2778 × 1284", 458,
                refresh_rate="10–120 Гц", promotion=True,
            ),
            body(78.1, 160.8, 7.65, 240, "Нержавеющая сталь и стекло"),
            connector="Lightning",
            camera_main="12 Мп",
            camera_ultrawide="12 Мп",
            camera_telephoto="12 Мп 3x",
        ),
    },

    # ------------------------------------------------------------------
    # iPhone 14
    # ------------------------------------------------------------------
    {
        "name": "iPhone 14",
        "slug": "iphone-14",
        "storage": ["128GB", "256GB", "512GB"],
        "colors": ["Midnight", "Purple", "Starlight", "(PRODUCT)RED", "Blue", "Yellow"],
        "specifications": specs(
            2022, "A15 Bionic",
            display(6.1, "2532 × 1170", 460),
            body(71.5, 146.7, 7.8, 172, "Алюминий и стекло"),
            connector="Lightning",
            camera_main="12 Мп",
            camera_ultrawide="12 Мп",
        ),
    },
    {
        "name": "iPhone 14 Plus",
        "slug": "iphone-14-plus",
        "storage": ["128GB", "256GB", "512GB"],
        "colors": ["Midnight", "Purple", "Starlight", "(PRODUCT)RED", "Blue", "Yellow"],
        "specifications": specs(
            2022, "A15 Bionic",
            display(6.7, "2778 × 1284", 458),
            body(78.1, 160.8, 7.8, 203, "Алюминий и стекло"),
            connector="Lightning",
            camera_main="12 Мп",
            camera_ultrawide="12 Мп",
        ),
    },
    {
        "name": "iPhone 14 Pro",
        "slug": "iphone-14-pro",
        "storage": ["128GB", "256GB", "512GB", "1TB"],
        "colors": ["Space Black", "Silver", "Gold", "Deep Purple"],
        "specifications": specs(
            2022, "A16 Bionic",
            display(
                6.1, "2556 × 1179", 460,
                refresh_rate="1–120 Гц",
                promotion=True,
                always_on=True,
                dynamic_island=True,
            ),
            body(71.5, 147.5, 7.85, 206, "Нержавеющая сталь и стекло"),
            connector="Lightning",
            camera_main="48 Мп",
            camera_ultrawide="12 Мп",
            camera_telephoto="12 Мп 3x",
        ),
    },
    {
        "name": "iPhone 14 Pro Max",
        "slug": "iphone-14-pro-max",
        "storage": ["128GB", "256GB", "512GB", "1TB"],
        "colors": ["Space Black", "Silver", "Gold", "Deep Purple"],
        "specifications": specs(
            2022, "A16 Bionic",
            display(
                6.7, "2796 × 1290", 460,
                refresh_rate="1–120 Гц",
                promotion=True,
                always_on=True,
                dynamic_island=True,
            ),
            body(77.6, 160.7, 7.85, 240, "Нержавеющая сталь и стекло"),
            connector="Lightning",
            camera_main="48 Мп",
            camera_ultrawide="12 Мп",
            camera_telephoto="12 Мп 3x",
        ),
    },

    # ------------------------------------------------------------------
    # iPhone 15
    # ------------------------------------------------------------------
    {
        "name": "iPhone 15",
        "slug": "iphone-15",
        "storage": ["128GB", "256GB", "512GB"],
        "colors": ["Black", "Blue", "Green", "Yellow", "Pink"],
        "specifications": specs(
            2023, "A16 Bionic",
            display(6.1, "2556 × 1179", 460, dynamic_island=True),
            body(71.6, 147.6, 7.8, 171, "Алюминий и стекло"),
            connector="USB-C",
            camera_main="48 Мп",
            camera_ultrawide="12 Мп",
        ),
    },
    {
        "name": "iPhone 15 Plus",
        "slug": "iphone-15-plus",
        "storage": ["128GB", "256GB", "512GB"],
        "colors": ["Black", "Blue", "Green", "Yellow", "Pink"],
        "specifications": specs(
            2023, "A16 Bionic",
            display(6.7, "2796 × 1290", 460, dynamic_island=True),
            body(77.8, 160.9, 7.8, 201, "Алюминий и стекло"),
            connector="USB-C",
            camera_main="48 Мп",
            camera_ultrawide="12 Мп",
        ),
    },
    {
        "name": "iPhone 15 Pro",
        "slug": "iphone-15-pro",
        "storage": ["128GB", "256GB", "512GB", "1TB"],
        "colors": ["Black Titanium", "White Titanium", "Blue Titanium", "Natural Titanium"],
        "specifications": specs(
            2023, "A17 Pro",
            display(
                6.1, "2556 × 1179", 460,
                refresh_rate="1–120 Гц",
                promotion=True,
                always_on=True,
                dynamic_island=True,
            ),
            body(70.6, 146.6, 8.25, 187, "Титан и стекло"),
            connector="USB-C",
            camera_main="48 Мп",
            camera_ultrawide="12 Мп",
            camera_telephoto="12 Мп 3x",
            apple_intelligence=True,
        ),
    },
    {
        "name": "iPhone 15 Pro Max",
        "slug": "iphone-15-pro-max",
        "storage": ["256GB", "512GB", "1TB"],
        "colors": ["Black Titanium", "White Titanium", "Blue Titanium", "Natural Titanium"],
        "specifications": specs(
            2023, "A17 Pro",
            display(
                6.7, "2796 × 1290", 460,
                refresh_rate="1–120 Гц",
                promotion=True,
                always_on=True,
                dynamic_island=True,
            ),
            body(76.7, 159.9, 8.25, 221, "Титан и стекло"),
            connector="USB-C",
            camera_main="48 Мп",
            camera_ultrawide="12 Мп",
            camera_telephoto="12 Мп 5x",
            apple_intelligence=True,
        ),
    },

    # ------------------------------------------------------------------
    # iPhone 16
    # ------------------------------------------------------------------
    {
        "name": "iPhone 16",
        "slug": "iphone-16",
        "storage": ["128GB", "256GB", "512GB"],
        "colors": ["Black", "White", "Pink", "Teal", "Ultramarine"],
        "specifications": specs(
            2024, "A18",
            display(6.1, "2556 × 1179", 460, dynamic_island=True),
            body(71.6, 147.6, 7.8, 170, "Алюминий и стекло"),
            connector="USB-C",
            camera_main="48 Мп Fusion",
            camera_ultrawide="12 Мп",
            apple_intelligence=True,
        ),
    },
    {
        "name": "iPhone 16 Plus",
        "slug": "iphone-16-plus",
        "storage": ["128GB", "256GB", "512GB"],
        "colors": ["Black", "White", "Pink", "Teal", "Ultramarine"],
        "specifications": specs(
            2024, "A18",
            display(6.7, "2796 × 1290", 460, dynamic_island=True),
            body(77.8, 160.9, 7.8, 199, "Алюминий и стекло"),
            connector="USB-C",
            camera_main="48 Мп Fusion",
            camera_ultrawide="12 Мп",
            apple_intelligence=True,
        ),
    },
    {
        "name": "iPhone 16 Pro",
        "slug": "iphone-16-pro",
        "storage": ["128GB", "256GB", "512GB", "1TB"],
        "colors": ["Black Titanium", "White Titanium", "Natural Titanium", "Desert Titanium"],
        "specifications": specs(
            2024, "A18 Pro",
            display(
                6.3, "2622 × 1206", 460,
                refresh_rate="1–120 Гц",
                promotion=True,
                always_on=True,
                dynamic_island=True,
            ),
            body(71.5, 149.6, 8.25, 199, "Титан и стекло"),
            connector="USB-C",
            camera_main="48 Мп Fusion",
            camera_ultrawide="48 Мп",
            camera_telephoto="12 Мп 5x",
            apple_intelligence=True,
        ),
    },
    {
        "name": "iPhone 16 Pro Max",
        "slug": "iphone-16-pro-max",
        "storage": ["256GB", "512GB", "1TB"],
        "colors": ["Black Titanium", "White Titanium", "Natural Titanium", "Desert Titanium"],
        "specifications": specs(
            2024, "A18 Pro",
            display(
                6.9, "2868 × 1320", 460,
                refresh_rate="1–120 Гц",
                promotion=True,
                always_on=True,
                dynamic_island=True,
            ),
            body(77.6, 163.0, 8.25, 227, "Титан и стекло"),
            connector="USB-C",
            camera_main="48 Мп Fusion",
            camera_ultrawide="48 Мп",
            camera_telephoto="12 Мп 5x",
            apple_intelligence=True,
        ),
    },
    {
        "name": "iPhone 16e",
        "slug": "iphone-16e",
        "storage": ["128GB", "256GB", "512GB"],
        "colors": ["Black", "White"],
        "specifications": specs(
            2025, "A18",
            display(6.1, "2532 × 1170", 460),
            body(71.5, 146.7, 7.8, 167, "Алюминий и стекло"),
            connector="USB-C",
            camera_main="48 Мп Fusion",
            camera_ultrawide=None,
            magsafe=False,
            apple_intelligence=True,
        ),
    },

    # ------------------------------------------------------------------
    # Линейка 2025: iPhone 17 / iPhone Air / iPhone 17 Pro
    # ------------------------------------------------------------------
    {
        "name": "iPhone 17",
        "slug": "iphone-17",
        "storage": ["256GB", "512GB"],
        "colors": ["Black", "White", "Mist Blue", "Sage", "Lavender"],
        "specifications": specs(
            2025, "A19",
            display(
                6.3, "2622 × 1206", 460,
                refresh_rate="1–120 Гц",
                promotion=True,
                always_on=True,
                dynamic_island=True,
            ),
            body(71.5, 149.6, 7.95, 177, "Алюминий и стекло"),
            connector="USB-C",
            camera_main="48 Мп Fusion",
            camera_ultrawide="48 Мп",
            camera_front="18 Мп Center Stage",
            apple_intelligence=True,
        ),
    },
    {
        "name": "iPhone Air",
        "slug": "iphone-air",
        "storage": ["256GB", "512GB", "1TB"],
        "colors": ["Space Black", "Cloud White", "Light Gold", "Sky Blue"],
        "specifications": specs(
            2025, "A19 Pro",
            display(
                6.5, "2736 × 1260", 460,
                refresh_rate="1–120 Гц",
                promotion=True,
                always_on=True,
                dynamic_island=True,
            ),
            body(74.7, 156.2, 5.64, 165, "Титан, Ceramic Shield 2 и Ceramic Shield"),
            connector="USB-C",
            camera_main="48 Мп Fusion",
            camera_ultrawide=None,
            camera_front="18 Мп Center Stage",
            apple_intelligence=True,
        ),
    },
    {
        "name": "iPhone 17 Pro",
        "slug": "iphone-17-pro",
        "storage": ["256GB", "512GB", "1TB"],
        "colors": ["Silver", "Cosmic Orange", "Deep Blue"],
        "specifications": specs(
            2025, "A19 Pro",
            display(
                6.3, "2622 × 1206", 460,
                refresh_rate="1–120 Гц",
                promotion=True,
                always_on=True,
                dynamic_island=True,
            ),
            body(71.9, 150.0, 8.75, 204, "Алюминиевый unibody, Ceramic Shield 2 и Ceramic Shield"),
            connector="USB-C",
            camera_main="48 Мп Fusion",
            camera_ultrawide="48 Мп",
            camera_telephoto="48 Мп",
            camera_front="18 Мп Center Stage",
            apple_intelligence=True,
        ),
    },
    {
        "name": "iPhone 17 Pro Max",
        "slug": "iphone-17-pro-max",
        "storage": ["256GB", "512GB", "1TB", "2TB"],
        "colors": ["Silver", "Cosmic Orange", "Deep Blue"],
        "specifications": specs(
            2025, "A19 Pro",
            display(
                6.9, "2868 × 1320", 460,
                refresh_rate="1–120 Гц",
                promotion=True,
                always_on=True,
                dynamic_island=True,
            ),
            body(78.0, 163.4, 8.75, 231, "Алюминиевый unibody, Ceramic Shield 2 и Ceramic Shield"),
            connector="USB-C",
            camera_main="48 Мп Fusion",
            camera_ultrawide="48 Мп",
            camera_telephoto="48 Мп",
            camera_front="18 Мп Center Stage",
            apple_intelligence=True,
        ),
    },
]


def storage_sort_key(value):
    if value.endswith("TB"):
        return int(value[:-2]) * 1024
    return int(value[:-2])


class Command(BaseCommand):
    help = "Создает/обновляет каталог Apple iPhone 11 и новее"

    @transaction.atomic
    def handle(self, *args, **options):
        brand, _ = Brand.objects.update_or_create(
            slug="apple",
            defaults={"name": "Apple"},
        )

        category, _ = Category.objects.update_or_create(
            slug="iphone",
            defaults={
                "name": "iPhone",
                "description": "Смартфоны Apple iPhone",
            },
        )

        all_storage = sorted(
            {value for item in IPHONES for value in item["storage"]},
            key=storage_sort_key,
        )
        all_colors = sorted(
            {value for item in IPHONES for value in item["colors"]},
        )

        storage_attribute, _ = Attribute.objects.update_or_create(
            slug="storage",
            defaults={
                "name": "Объем памяти",
                "applies_to": "variant",
                "type": "enum",
                "is_required": True,
                "sort_order": 10,
                "unit": "",
                "group_name": "Основные характеристики",
                "values": all_storage,
            },
        )

        color_attribute, _ = Attribute.objects.update_or_create(
            slug="color",
            defaults={
                "name": "Цвет",
                "applies_to": "variant",
                "type": "enum",
                "is_required": True,
                "sort_order": 20,
                "unit": "",
                "group_name": "Внешний вид",
                "values": all_colors,
            },
        )

        category.attributes.add(storage_attribute, color_attribute)
        register_attributes(Attribute, category)

        products_created = 0
        products_updated = 0
        variants_created = 0
        variants_existing = 0

        for item in IPHONES:
            product, created = Product.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "brand": brand,
                    "category": category,
                    "short_description": f"Apple {item['name']}",
                    "description": (
                        f"{item['name']} — смартфон Apple. "
                        "Выберите цвет и объем памяти в доступных вариантах."
                    ),
                    "seo_title": f"Купить {item['name']} — цена и характеристики",
                    "seo_description": (
                        f"{item['name']}: характеристики, цвета, объемы памяти, "
                        "цены и наличие."
                    ),
                    "specifications": normalize_specifications(item["specifications"]),
                    "is_active": True,
                },
            )

            if created:
                products_created += 1
                action = "создан"
            else:
                products_updated += 1
                action = "обновлен"

            self.stdout.write(f"{product.name}: {action}")

            for storage in item["storage"]:
                for color in item["colors"]:
                    attrs = {
                        "storage": storage,
                        "color": color,
                    }

                    # Не используем SKU как ключ импорта:
                    # артикулы магазина могут быть собственными.
                    existing_variant = ProductVariant.objects.filter(
                        product=product,
                        attributes=attrs,
                    ).first()

                    if existing_variant:
                        variants_existing += 1
                        continue

                    ProductVariant.objects.create(
                        product=product,
                        attributes=attrs,
                        sku=None,
                        price=0,
                        old_price=None,
                        stock=0,
                        is_active=False,
                    )
                    variants_created += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Импорт iPhone завершен."))
        self.stdout.write(
            f"Товары: создано {products_created}, обновлено {products_updated}"
        )
        self.stdout.write(
            f"Варианты: создано {variants_created}, уже существовало {variants_existing}"
        )
        self.stdout.write(
            self.style.WARNING(
                "Новые варианты созданы неактивными с ценой 0 и остатком 0. "
                "Укажите реальные цены/остатки и активируйте нужные варианты."
            )
        )
