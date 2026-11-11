# Использование официального легкого образа Python
FROM python:3.11-slim

# Настройка переменных окружения для корректной работы Python в контейнере
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Установка рабочей директории
WORKDIR /app

# Копирование файла зависимостей и их установка
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всех исходных файлов проекта
COPY . .

# Открытие порта приложения
EXPOSE 8000

# Команда для запуска FastAPI через Uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]