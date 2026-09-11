"""Versioned iPhone schema shared with migration 0019. Keep v1 immutable."""

# source path, canonical slug, label, type, unit, group
SPECIFICATIONS = (
    ('year', 'release-year', 'Год выпуска', 'number', '', 'Основные характеристики'),
    ('chip.name', 'processor', 'Процессор', 'string', '', 'Производительность'),
    ('display.type', 'display-type', 'Тип экрана', 'string', '', 'Экран'),
    ('display.size_inches', 'screen-size', 'Диагональ экрана', 'number', 'дюйм', 'Экран'),
    ('display.resolution', 'resolution', 'Разрешение', 'string', '', 'Экран'),
    ('display.ppi', 'pixel-density', 'Плотность пикселей', 'number', 'ppi', 'Экран'),
    ('display.refresh_rate', 'refresh-rate', 'Частота обновления', 'string', '', 'Экран'),
    ('display.promotion', 'promotion', 'ProMotion', 'enum', '', 'Экран'),
    ('display.always_on', 'always-on', 'Always-On Display', 'enum', '', 'Экран'),
    ('display.dynamic_island', 'dynamic-island', 'Dynamic Island', 'enum', '', 'Экран'),
    ('camera.main', 'camera-main', 'Основная камера', 'string', '', 'Камеры'),
    ('camera.front', 'camera-front', 'Фронтальная камера', 'string', '', 'Камеры'),
    ('camera.ultrawide', 'camera-ultrawide', 'Сверхширокоугольная камера', 'string', '', 'Камеры'),
    ('camera.telephoto', 'camera-telephoto', 'Телефотокамера', 'string', '', 'Камеры'),
    ('body.width_mm', 'width', 'Ширина', 'number', 'мм', 'Корпус'),
    ('body.height_mm', 'height', 'Высота', 'number', 'мм', 'Корпус'),
    ('body.depth_mm', 'depth', 'Толщина', 'number', 'мм', 'Корпус'),
    ('body.weight_g', 'weight', 'Вес', 'number', 'г', 'Корпус'),
    ('body.material', 'body-material', 'Материал корпуса', 'string', '', 'Корпус'),
    ('body.water_resistance', 'water-resistance', 'Защита от воды и пыли', 'string', '', 'Корпус'),
    ('connector', 'connector', 'Разъём', 'string', '', 'Подключение'),
    ('5g', '5g', 'Поддержка 5G', 'enum', '', 'Подключение'),
    ('magsafe', 'magsafe', 'MagSafe', 'enum', '', 'Возможности'),
    ('face_id', 'face-id', 'Face ID', 'enum', '', 'Возможности'),
    ('apple_intelligence', 'apple-intelligence', 'Apple Intelligence', 'enum', '', 'Возможности'),
)


def normalize_specifications(specifications):
    from copy import deepcopy

    result = deepcopy(specifications or {})
    for path, slug, _name, _type, _unit, _group in SPECIFICATIONS:
        parts = path.split('.')
        parent = result
        if len(parts) == 2:
            parent = result.get(parts[0])
            if not isinstance(parent, dict):
                continue
        key = parts[-1]
        if key not in parent:
            continue
        value = parent[key]
        if isinstance(value, bool):
            value = 'Да' if value else 'Нет'
        # Preserve both values on conflict instead of silently discarding data.
        if slug != path and slug in result and result[slug] != value:
            continue
        del parent[key]
        if len(parts) == 2 and not parent:
            del result[parts[0]]
        result[slug] = value
    return result


def register_attributes(attribute_model, category, using='default'):
    for index, (_path, slug, name, kind, unit, group) in enumerate(SPECIFICATIONS, 1):
        attribute, _ = attribute_model.objects.using(using).update_or_create(
            slug=slug,
            defaults={
                'name': name, 'applies_to': 'product', 'type': kind,
                'unit': unit, 'group_name': group, 'sort_order': index * 10,
                'is_required': False, 'values': ['Да', 'Нет'] if kind == 'enum' else None,
            },
        )
        category.attributes.add(attribute)
