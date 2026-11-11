#!/bin/bash
set -e

echo "Запуск міграцій Django..."
python manage.py makemigrations quotes
python manage.py migrate
echo "Запуск міграції даних з MongoDB..."
python migrate_mongo_to_postgres.py || echo "Міграція з MongoDB пропущена або завершилась з помилкою"

echo "Запуск сервера Django..."
exec "$@"