#!/bin/bash
cd /home/pavel/electronics-store-back

# Активируем venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "ERROR: Virtual environment not found!"
    exit 1
fi

# Устанавливаем переменные окружения
export PYTHONPATH="/home/pavel/electronics-store-back/src:$PYTHONPATH"
export DJANGO_SETTINGS_MODULE="core.settings"

echo "Starting Django server..."
echo "PYTHONPATH: $PYTHONPATH"
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"

# Запускаем сервер
exec python manage.py runserver 0.0.0.0:8000
