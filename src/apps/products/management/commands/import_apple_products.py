"""
Импорт каталога Apple: iPad, MacBook, Apple Watch и Mac.

Размещение:
    <your_app>/management/commands/import_apple_products.py

Запуск:
    python manage.py import_apple_products

Повторный запуск безопасен:
- Brand / Category / Attribute / Product обновляются через update_or_create;
- значения enum-атрибутов объединяются с уже существующими (не затирают iPhone);
- ProductVariant ищется по product + attributes;
- существующие price / old_price / stock / is_active у вариантов НЕ перезаписываются.

ВАЖНО:
Новые варианты создаются с price=0, stock=0, is_active=False, чтобы импорт
характеристик случайно не выставил товар в продажу.
"""

from itertools import product as cartesian_product

from django.core.management.base import BaseCommand
from django.db import transaction

from ...models import Brand, Category, Attribute, Product, ProductVariant


def merge_variant_enum_attribute(*, slug, name, values, sort_order, group_name):
    """Создаёт variant enum или дополняет существующий без изменения его схемы."""
    attribute = Attribute.objects.filter(slug=slug).first()
    if attribute is None:
        attribute = Attribute.objects.filter(name=name).first()

    if attribute is not None:
        existing_values = list(attribute.values or [])
        merged_values = list(dict.fromkeys([*existing_values, *values]))
        if merged_values != existing_values:
            attribute.values = merged_values
            attribute.save(update_fields=["values"])
        return attribute

    return Attribute.objects.create(
        slug=slug,
        name=name,
        applies_to="variant",
        type="enum",
        is_required=True,
        sort_order=sort_order,
        unit="",
        group_name=group_name,
        values=list(dict.fromkeys(values)),
    )


def ensure_product_attribute(*, slug, name, type="string", sort_order=0, unit="", group_name="", values=None):
    """Возвращает существующий product-атрибут либо создаёт новый с уникальными slug/name."""
    attribute = Attribute.objects.filter(slug=slug).first()
    if attribute is None:
        attribute = Attribute.objects.filter(name=name).first()
    if attribute is not None:
        return attribute
    return Attribute.objects.create(
        slug=slug,
        name=name,
        applies_to="product",
        type=type,
        is_required=False,
        sort_order=sort_order,
        unit=unit,
        group_name=group_name,
        values=values,
    )


def yes_no(value):
    return "Да" if value else "Нет"


def ipad_specs(year, chip, size, resolution, *, display_type="Liquid Retina", promotion=False,
               apple_intelligence=True, camera="12 Мп", connector="USB-C"):
    return {
        "release-year": year,
        "processor": chip,
        "screen-size": size,
        "display-type": display_type,
        "resolution": resolution,
        "promotion": yes_no(promotion),
        "camera-main": camera,
        "camera-front": "12 Мп",
        "connector": connector,
        "apple-intelligence": yes_no(apple_intelligence),
    }


def macbook_specs(year, chip, size, resolution, *, display_type="Liquid Retina",
                  promotion=False, battery_hours=None, apple_intelligence=True):
    data = {
        "release-year": year,
        "processor": chip,
        "screen-size": size,
        "display-type": display_type,
        "resolution": resolution,
        "promotion": yes_no(promotion),
        "body-material": "Алюминий",
        "connector": "USB-C / Thunderbolt",
        "apple-intelligence": yes_no(apple_intelligence),
    }
    if battery_hours:
        data["battery-life"] = battery_hours
    return data


def watch_specs(year, chip, *, display_size, material, water_resistance,
                gps=True, cellular=True, health_sensing=True):
    return {
        "release-year": year,
        "processor": chip,
        "watch-display-size": display_size,
        "body-material": material,
        "water-resistance": water_resistance,
        "always-on": "Да",
        "gps": yes_no(gps),
        "cellular": yes_no(cellular),
        "health-sensing": yes_no(health_sensing),
    }


def mac_specs(year, chip, *, form_factor, memory_max=None, storage_max=None,
              display=None, apple_intelligence=True):
    data = {
        "release-year": year,
        "processor": chip,
        "form-factor": form_factor,
        "apple-intelligence": yes_no(apple_intelligence),
    }
    if memory_max:
        data["memory-max"] = memory_max
    if storage_max:
        data["storage-max"] = storage_max
    if display:
        if display.get("type"):
            data["display-type"] = display["type"]
        if display.get("size_inches") is not None:
            data["screen-size"] = display["size_inches"]
        if display.get("resolution"):
            data["resolution"] = display["resolution"]
    return data


CATEGORIES = {
    "ipad": {
        "slug": "ipadmac",
        "name": "iPad",
        "description": "Планшеты Apple iPad",
    },
    "macbook": {
        "slug": "macbook",
        "name": "MacBook",
        "description": "Ноутбуки Apple MacBook",
    },
    "watch": {
        "slug": "apple-watch",
        "name": "Apple Watch",
        "description": "Умные часы Apple Watch",
    },
    "mac": {
        "slug": "mac",
        "name": "Mac",
        "description": "Настольные компьютеры Apple Mac",
    },
}


IPADS = [
    {
        "name": "iPad (A16)",
        "slug": "ipad-a16",
        "storage": ["128GB", "256GB", "512GB"],
        "colors": ["Blue", "Pink", "Yellow", "Silver"],
        "connectivity": ["Wi‑Fi", "Wi‑Fi + Cellular"],
        "specifications": ipad_specs(
            2025, "A16", 11.0, "2360 × 1640", apple_intelligence=False
        ),
    },
    {
        "name": "iPad mini (A17 Pro)",
        "slug": "ipad-mini-a17-pro",
        "storage": ["128GB", "256GB", "512GB"],
        "colors": ["Blue", "Purple", "Starlight", "Space Gray"],
        "connectivity": ["Wi‑Fi", "Wi‑Fi + Cellular"],
        "specifications": ipad_specs(
            2024, "A17 Pro", 8.3, "2266 × 1488", apple_intelligence=True
        ),
    },
    {
        "name": "iPad Air 11 (M4)",
        "slug": "ipad-air-11-m4",
        "storage": ["128GB", "256GB", "512GB", "1TB"],
        "colors": ["Blue", "Purple", "Starlight", "Space Gray"],
        "connectivity": ["Wi‑Fi", "Wi‑Fi + Cellular"],
        "specifications": ipad_specs(2026, "M4", 11.0, "2360 × 1640"),
    },
    {
        "name": "iPad Air 13 (M4)",
        "slug": "ipad-air-13-m4",
        "storage": ["128GB", "256GB", "512GB", "1TB"],
        "colors": ["Blue", "Purple", "Starlight", "Space Gray"],
        "connectivity": ["Wi‑Fi", "Wi‑Fi + Cellular"],
        "specifications": ipad_specs(2026, "M4", 13.0, "2732 × 2048"),
    },
    {
        "name": "iPad Pro 11 (M5)",
        "slug": "ipad-pro-11-m5",
        "storage": ["256GB", "512GB", "1TB", "2TB"],
        "colors": ["Silver", "Space Black"],
        "connectivity": ["Wi‑Fi", "Wi‑Fi + Cellular"],
        "specifications": ipad_specs(
            2025, "M5", 11.0, "2420 × 1668",
            display_type="Ultra Retina XDR tandem OLED", promotion=True,
        ),
    },
    {
        "name": "iPad Pro 13 (M5)",
        "slug": "ipad-pro-13-m5",
        "storage": ["256GB", "512GB", "1TB", "2TB"],
        "colors": ["Silver", "Space Black"],
        "connectivity": ["Wi‑Fi", "Wi‑Fi + Cellular"],
        "specifications": ipad_specs(
            2025, "M5", 13.0, "2752 × 2064",
            display_type="Ultra Retina XDR tandem OLED", promotion=True,
        ),
    },
]


MACBOOKS = [
    {
        "name": "MacBook Neo 13 (A18 Pro)",
        "slug": "macbook-neo-13-a18-pro",
        "storage": ["256GB", "512GB"],
        "memory": ["8GB"],
        "colors": ["Silver", "Blush", "Citrus", "Indigo"],
        "chips": ["A18 Pro"],
        "specifications": macbook_specs(
            2026, "A18 Pro", 13.0, "2408 × 1506", battery_hours=16
        ),
    },
    {
        "name": "MacBook Air 13 (M5)",
        "slug": "macbook-air-13-m5",
        "storage": ["512GB", "1TB", "2TB", "4TB"],
        "memory": ["16GB", "24GB", "32GB"],
        "colors": ["Sky Blue", "Silver", "Starlight", "Midnight"],
        "chips": ["M5"],
        "specifications": macbook_specs(
            2026, "M5", 13.6, "2560 × 1664", battery_hours=18
        ),
    },
    {
        "name": "MacBook Air 15 (M5)",
        "slug": "macbook-air-15-m5",
        "storage": ["512GB", "1TB", "2TB", "4TB"],
        "memory": ["16GB", "24GB", "32GB"],
        "colors": ["Sky Blue", "Silver", "Starlight", "Midnight"],
        "chips": ["M5"],
        "specifications": macbook_specs(
            2026, "M5", 15.3, "2880 × 1864", battery_hours=18
        ),
    },
    {
        "name": "MacBook Pro 14",
        "slug": "macbook-pro-14-m5",
        "storage": ["512GB", "1TB", "2TB", "4TB", "8TB"],
        "memory": ["16GB", "24GB", "32GB", "48GB", "64GB", "128GB"],
        "colors": ["Space Black", "Silver"],
        "chips": ["M5", "M5 Pro", "M5 Max"],
        "specifications": macbook_specs(
            2026, "M5 / M5 Pro / M5 Max", 14.2, "3024 × 1964",
            display_type="Liquid Retina XDR", promotion=True, battery_hours=24,
        ),
    },
    {
        "name": "MacBook Pro 16",
        "slug": "macbook-pro-16-m5-pro-max",
        "storage": ["512GB", "1TB", "2TB", "4TB", "8TB"],
        "memory": ["24GB", "36GB", "48GB", "64GB", "128GB"],
        "colors": ["Space Black", "Silver"],
        "chips": ["M5 Pro", "M5 Max"],
        "specifications": macbook_specs(
            2026, "M5 Pro / M5 Max", 16.2, "3456 × 2234",
            display_type="Liquid Retina XDR", promotion=True, battery_hours=24,
        ),
    },
]


WATCHES = [

    {
        "name": "Apple Watch SE 3",
        "slug": "apple-watch-se-3",
        "sizes": ["40mm", "44mm"],
        "colors": ["Midnight", "Starlight"],
        "connectivity": ["GPS", "GPS + Cellular"],
        "specifications": watch_specs(
            2025, "S10", display_size="40 / 44 мм",
            material="Алюминий", water_resistance="50 м",
        ),
    },
    {
        "name": "Apple Watch Series 12 Aluminum",
        "slug": "apple-watch-series-12-aluminum",
        "sizes": ["42mm", "46mm"],
        "colors": ["Dark Bronze", "Black", "Light Gold", "Space Gray"],
        "connectivity": ["GPS", "GPS + Cellular"],
        "specifications": watch_specs(
            2026, "S11", display_size="42 / 46 мм",
            material="Алюминий", water_resistance="50 м",
        ),
    },
    {
        "name": "Apple Watch Series 12 Titanium",
        "slug": "apple-watch-series-12-titanium",
        "sizes": ["42mm", "46mm"],
        "colors": ["Radiant Gold", "Natural Titanium"],
        "connectivity": ["GPS + Cellular"],
        "specifications": watch_specs(
            2026, "S11", display_size="42 / 46 мм",
            material="Титан", water_resistance="50 м",
        ),
    },
    {
        "name": "Apple Watch Series 12 Ceramic",
        "slug": "apple-watch-series-12-ceramic",
        "sizes": ["42mm", "46mm"],
        "colors": ["Pearl White", "Night Blue"],
        "connectivity": ["GPS + Cellular"],
        "specifications": watch_specs(
            2026, "S11", display_size="42 / 46 мм",
            material="Керамика", water_resistance="50 м",
        ),
    },
    {
        "name": "Apple Watch Ultra 4",
        "slug": "apple-watch-ultra-4",
        "sizes": ["49mm"],
        "colors": ["Natural Titanium", "Black Titanium"],
        "connectivity": ["GPS + Cellular"],
        "specifications": watch_specs(
            2026, "S11", display_size="49 мм",
            material="Титан", water_resistance="100 м",
        ),
    },
]


MACS = [

    {
        "name": "Mac Studio (M5 Max)",
        "slug": "mac-studio-m5-max",
        "storage": ["512GB", "1TB", "2TB", "4TB", "8TB"],
        "memory": ["36GB", "48GB", "64GB", "128GB"],
        "colors": ["Silver"],
        "chips": ["M5 Max"],
        "specifications": mac_specs(
            2026, "M5 Max", form_factor="Mac Studio", memory_max="128GB", storage_max="8TB"
        ),
    },
    {
        "name": "Mac Studio (M5 Ultra)",
        "slug": "mac-studio-m5-ultra",
        "storage": ["1TB", "2TB", "4TB", "8TB", "16TB"],
        "memory": ["96GB", "256GB", "512GB"],
        "colors": ["Silver"],
        "chips": ["M5 Ultra"],
        "specifications": mac_specs(
            2026, "M5 Ultra", form_factor="Mac Studio", memory_max="512GB", storage_max="16TB"
        ),
    },
    {
        "name": "Mac mini (M4)",
        "slug": "mac-mini-m4",
        "storage": ["256GB", "512GB", "1TB", "2TB"],
        "memory": ["16GB", "24GB", "32GB"],
        "colors": ["Silver"],
        "chips": ["M4"],
        "specifications": mac_specs(
            2024, "M4", form_factor="Mac mini", memory_max="32GB", storage_max="2TB"
        ),
    },
    {
        "name": "Mac mini (M4 Pro)",
        "slug": "mac-mini-m4-pro",
        "storage": ["512GB", "1TB", "2TB", "4TB", "8TB"],
        "memory": ["24GB", "48GB", "64GB"],
        "colors": ["Silver"],
        "chips": ["M4 Pro"],
        "specifications": mac_specs(
            2024, "M4 Pro", form_factor="Mac mini", memory_max="64GB", storage_max="8TB"
        ),
    },
    {
        "name": "Mac mini (M6)",
        "slug": "mac-mini-m6",
        "storage": ["512GB", "1TB", "2TB"],
        "memory": ["16GB", "24GB", "32GB"],
        "colors": ["Silver"],
        "chips": ["M6"],
        "specifications": mac_specs(
            2026, "M6", form_factor="Mac mini", memory_max="32GB", storage_max="2TB"
        ),
    },
    {
        "name": "Mac mini (M5 Pro)",
        "slug": "mac-mini-m5-pro",
        "storage": ["512GB", "1TB", "2TB", "4TB", "8TB"],
        "memory": ["24GB", "48GB", "64GB"],
        "colors": ["Silver"],
        "chips": ["M5 Pro"],
        "specifications": mac_specs(
            2026, "M5 Pro", form_factor="Mac mini", memory_max="64GB", storage_max="8TB"
        ),
    },
    {
        "name": "iMac 24 (M4)",
        "slug": "imac-24-m4",
        "storage": ["256GB", "512GB", "1TB", "2TB"],
        "memory": ["16GB", "24GB", "32GB"],
        "colors": ["Blue", "Green", "Pink", "Silver", "Yellow", "Orange", "Purple"],
        "chips": ["M4"],
        "specifications": mac_specs(
            2024, "M4", form_factor="iMac",
            memory_max="32GB", storage_max="2TB",
            display={"type": "Retina 4.5K", "size_inches": 24, "resolution": "4480 × 2520"},
        ),
    },
    {
        "name": "Mac Studio (M4 Max)",
        "slug": "mac-studio-m4-max",
        "storage": ["512GB", "1TB", "2TB", "4TB", "8TB"],
        "memory": ["36GB", "48GB", "64GB", "128GB"],
        "colors": ["Silver"],
        "chips": ["M4 Max"],
        "specifications": mac_specs(
            2025, "M4 Max", form_factor="Mac Studio", memory_max="128GB", storage_max="8TB"
        ),
    },
    {
        "name": "Mac Studio (M3 Ultra)",
        "slug": "mac-studio-m3-ultra",
        "storage": ["1TB", "2TB", "4TB", "8TB", "16TB"],
        "memory": ["96GB", "256GB", "512GB"],
        "colors": ["Silver"],
        "chips": ["M3 Ultra"],
        "specifications": mac_specs(
            2025, "M3 Ultra", form_factor="Mac Studio", memory_max="512GB", storage_max="16TB"
        ),
    },
    {
        "name": "Mac Pro (M2 Ultra)",
        "slug": "mac-pro-m2-ultra",
        "storage": ["1TB", "2TB", "4TB", "8TB"],
        "memory": ["64GB", "128GB", "192GB"],
        "colors": ["Silver"],
        "chips": ["M2 Ultra"],
        "specifications": mac_specs(
            2023, "M2 Ultra", form_factor="Mac Pro", memory_max="192GB", storage_max="8TB"
        ),
    },
]


def collect_values(items, key):
    return sorted({value for item in items for value in item.get(key, [])})


def storage_sort_key(value):
    if value.endswith("TB"):
        return int(value[:-2]) * 1024
    if value.endswith("GB"):
        return int(value[:-2])
    return 0


def memory_sort_key(value):
    if value.endswith("GB"):
        return int(value[:-2])
    return 0


class Command(BaseCommand):
    help = "Создает/обновляет каталог Apple iPad, MacBook, Apple Watch и Mac"

    @transaction.atomic
    def handle(self, *args, **options):
        brand, _ = Brand.objects.update_or_create(
            slug="apple",
            defaults={"name": "Apple"},
        )

        categories = {}
        for key, data in CATEGORIES.items():
            category, _ = Category.objects.update_or_create(
                slug=data["slug"],
                defaults={"name": data["name"], "description": data["description"]},
            )
            categories[key] = category

        all_items = [*IPADS, *MACBOOKS, *WATCHES, *MACS]

        # Уже существующие variant-атрибуты iPhone переиспользуем и только
        # дополняем их values. Не меняем applies_to/type/name/slug.
        storage_attribute = merge_variant_enum_attribute(
            slug="storage",
            name="Объем памяти",
            values=sorted(collect_values(all_items, "storage"), key=storage_sort_key),
            sort_order=10,
            group_name="Основные характеристики",
        )
        color_attribute = merge_variant_enum_attribute(
            slug="color",
            name="Цвет",
            values=collect_values(all_items, "colors"),
            sort_order=20,
            group_name="Внешний вид",
        )

        # Новые variant-атрибуты имеют отдельные slug/name и не конфликтуют
        # с product-атрибутами connectivity/processor.
        memory_attribute = merge_variant_enum_attribute(
            slug="memory",
            name="Оперативная память",
            values=sorted(collect_values(all_items, "memory"), key=memory_sort_key),
            sort_order=30,
            group_name="Основные характеристики",
        )
        connection_attribute = merge_variant_enum_attribute(
            slug="connection-type",
            name="Тип подключения",
            values=collect_values(all_items, "connectivity"),
            sort_order=40,
            group_name="Связь",
        )
        watch_size_attribute = merge_variant_enum_attribute(
            slug="watch-case-size",
            name="Размер корпуса часов",
            values=collect_values(all_items, "sizes"),
            sort_order=50,
            group_name="Внешний вид",
        )
        processor_variant_attribute = merge_variant_enum_attribute(
            slug="processor-config",
            name="Конфигурация процессора",
            values=collect_values(all_items, "chips"),
            sort_order=60,
            group_name="Основные характеристики",
        )

        # Дополнительные product-атрибуты, которых нет в iphone_specifications_v1.
        ensure_product_attribute(slug="battery-life", name="Автономность", type="number", unit="ч", sort_order=260, group_name="Питание")
        ensure_product_attribute(slug="watch-display-size", name="Размер дисплея часов", sort_order=40, group_name="Экран")
        ensure_product_attribute(slug="gps", name="GPS", type="enum", sort_order=270, group_name="Связь", values=["Да", "Нет"])
        ensure_product_attribute(slug="cellular", name="Cellular", type="enum", sort_order=280, group_name="Связь", values=["Да", "Нет"])
        ensure_product_attribute(slug="health-sensing", name="Датчики здоровья", type="enum", sort_order=290, group_name="Возможности", values=["Да", "Нет"])
        ensure_product_attribute(slug="form-factor", name="Форм-фактор", sort_order=300, group_name="Основные характеристики")
        ensure_product_attribute(slug="memory-max", name="Максимальная оперативная память", sort_order=310, group_name="Основные характеристики")
        ensure_product_attribute(slug="storage-max", name="Максимальный накопитель", sort_order=320, group_name="Основные характеристики")

        # Привязываем к категориям product-атрибуты, которые используются в specifications.
        product_attribute_slugs = {
            "release-year", "processor", "screen-size", "display-type", "resolution",
            "promotion", "camera-main", "camera-front", "connector", "apple-intelligence",
            "body-material", "water-resistance", "always-on", "battery-life",
            "watch-display-size", "gps", "cellular", "health-sensing",
            "form-factor", "memory-max", "storage-max",
        }
        product_attributes = {
            a.slug: a for a in Attribute.objects.filter(slug__in=product_attribute_slugs)
        }

        categories["ipad"].attributes.add(
            storage_attribute, color_attribute, connection_attribute,
            *[product_attributes[s] for s in (
                "release-year", "processor", "screen-size", "display-type", "resolution",
                "promotion", "camera-main", "camera-front", "connector", "apple-intelligence",
            ) if s in product_attributes],
        )
        categories["macbook"].attributes.add(
            storage_attribute, color_attribute, memory_attribute, processor_variant_attribute,
            *[product_attributes[s] for s in (
                "release-year", "processor", "screen-size", "display-type", "resolution",
                "promotion", "body-material", "connector", "apple-intelligence", "battery-life",
            ) if s in product_attributes],
        )
        categories["watch"].attributes.add(
            color_attribute, connection_attribute, watch_size_attribute,
            *[product_attributes[s] for s in (
                "release-year", "processor", "watch-display-size", "body-material",
                "water-resistance", "always-on", "gps", "cellular", "health-sensing",
            ) if s in product_attributes],
        )
        categories["mac"].attributes.add(
            storage_attribute, color_attribute, memory_attribute, processor_variant_attribute,
            *[product_attributes[s] for s in (
                "release-year", "processor", "screen-size", "display-type", "resolution",
                "apple-intelligence", "form-factor", "memory-max", "storage-max",
            ) if s in product_attributes],
        )

        products_created = 0
        products_updated = 0
        variants_created = 0
        variants_existing = 0

        def upsert_product(item, category, variant_dimensions, description):
            nonlocal products_created, products_updated, variants_created, variants_existing

            product_obj, created = Product.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "brand": brand,
                    "category": category,
                    "short_description": f"Apple {item['name']}",
                    "description": description,
                    "seo_title": f"Купить {item['name']} — цена и характеристики",
                    "seo_description": (
                        f"{item['name']}: характеристики, конфигурации, цены и наличие."
                    ),
                    "specifications": item["specifications"],
                    "is_active": True,
                },
            )

            if created:
                products_created += 1
                action = "создан"
            else:
                products_updated += 1
                action = "обновлен"

            self.stdout.write(f"{product_obj.name}: {action}")

            dimensions = []
            for attr_slug, item_key in variant_dimensions:
                values = item.get(item_key, [])
                if values:
                    dimensions.append((attr_slug, values))

            if not dimensions:
                combinations = [()]
            else:
                combinations = cartesian_product(*(values for _, values in dimensions))

            for combination in combinations:
                attrs = {
                    dimensions[index][0]: value
                    for index, value in enumerate(combination)
                }

                existing_variant = ProductVariant.objects.filter(
                    product=product_obj,
                    attributes=attrs,
                ).first()

                if existing_variant:
                    variants_existing += 1
                    continue

                ProductVariant.objects.create(
                    product=product_obj,
                    attributes=attrs,
                    sku=None,
                    price=0,
                    old_price=None,
                    stock=0,
                    is_active=False,
                )
                variants_created += 1

        for item in IPADS:
            upsert_product(
                item,
                categories["ipad"],
                [
                    (storage_attribute.slug, "storage"),
                    (color_attribute.slug, "colors"),
                    (connection_attribute.slug, "connectivity"),
                ],
                f"{item['name']} — планшет Apple. Выберите память, цвет и тип подключения.",
            )

        for item in MACBOOKS:
            upsert_product(
                item,
                categories["macbook"],
                [
                    (processor_variant_attribute.slug, "chips"),
                    (memory_attribute.slug, "memory"),
                    (storage_attribute.slug, "storage"),
                    (color_attribute.slug, "colors"),
                ],
                f"{item['name']} — ноутбук Apple. Выберите процессор, память, накопитель и цвет.",
            )

        for item in WATCHES:
            upsert_product(
                item,
                categories["watch"],
                [
                    (watch_size_attribute.slug, "sizes"),
                    (color_attribute.slug, "colors"),
                    (connection_attribute.slug, "connectivity"),
                ],
                f"{item['name']} — умные часы Apple. Выберите размер, цвет и подключение.",
            )

        for item in MACS:
            upsert_product(
                item,
                categories["mac"],
                [
                    (processor_variant_attribute.slug, "chips"),
                    (memory_attribute.slug, "memory"),
                    (storage_attribute.slug, "storage"),
                    (color_attribute.slug, "colors"),
                ],
                f"{item['name']} — компьютер Apple. Выберите процессор, память и накопитель.",
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Импорт Apple-каталога завершен."))
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
