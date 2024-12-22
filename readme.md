# Тестовое задание на python разработчика

Необходимые переменные окружения находятся в env.template.

Для запуска сервисов c помощью docker:
1. Переименовать env.template в env.dev, при необходимости задать свои значения переменных.
2. Запустить сервисы: `docker compose -f dc-dev.yml up -d --build`
Сервисы поднимаются на портах 8081, 8082. 
3. Отдельно поднять только БД: `docker compose -f dc-dev.yml up -d db`

Остановить сервисы: `docker compose -f dc-dev.yml down -v`

Для запуска сервисов без контейнеров:
1. Создать виртуальное окружение (например, [venv](https://docs.python.org/3/library/venv.html))
2. Установить зависимости: `pip install -r requirements.txt -r requirements.dev.txt`
3. Запуск сервиса авторизации: `python src/auth_main.py` (порт 8081)
4. Запуск сервиса транзакций: `python src/trans_main.py` (порт 8082)

Для запуска тестов: `python -m pytest tests`