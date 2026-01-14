(function ($) {
    $(document).ready(function () {
        // Находим поле категории
        var $categoryField = $('#id_category');

        if ($categoryField.length) {
            // При изменении категории
            $categoryField.change(function () {
                var categoryId = $(this).val();
                if (categoryId) {
                    // Можно добавить логику для AJAX-загрузки атрибутов
                    // или просто перезагрузить страницу
                    console.log('Category changed to:', categoryId);
                }
            });
        }

        // Добавляем кнопку для обновления атрибутов
        $('.field-category').append(
            '<button type="button" class="button update-attributes-btn" style="margin-left: 10px;">Обновить атрибуты</button>',
        );

        $('.update-attributes-btn').click(function () {
            // Перезагружаем страницу для обновления полей вариантов
            location.reload();
        });
    });
})(django.jQuery);
