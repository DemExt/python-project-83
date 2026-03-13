# Page Analyzer (Анализатор страниц)

### Hexlet tests and linter status:
[![Actions Status](https://github.com/DemExt/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/DemExt/python-project-83/actions)

[![SonarQube Cloud](https://sonarcloud.io/images/project_badges/sonarcloud-light.svg)](https://sonarcloud.io/summary/new_code?id=DemExt_python-project-83)

## Описание
Многофункциональный веб-анализатор, который проверяет указанные сайты на доступность и парсит SEO-данные (теги H1, Title, Description). Результаты проверок сохраняются в базе данных PostgreSQL для последующего анализа.

## Основные возможности:
* Валидация и нормализация вводимых URL.
* Проверка статус-кода ответа сервера.
* Извлечение мета-данных страниц (SEO-анализ).
* История проверок для каждого добавленного сайта.

## Установка и запуск

1. Требования
* Python 3.10+
* PostgreSQL
* **uv** (менеджер пакетов)

2. Клонирование репозитория
```bash
git clone https://github.com/DemExt/python-project-83.git
cd python-project-83
uv sync

3. Установка зависимостей
bash
make install

4. Настройка окружения
Создайте файл .env в корне проекта и добавьте в него секретный ключ и строку подключения к БД:
env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=your_very_secret_key

5. Инициализация базы данных
Выполните команды из файла database.sql в вашем клиенте PostgreSQL или через терминал:
bash
psql -d dbname -f database.sql

6. Запуск приложения
uv run flask --app page_analyzer:app run

Приложение будет доступно по адресу: http://localhost:5000
Инструменты разработки
Flask — веб-фреймворк.
PostgreSQL — база данных.
BeautifulSoup4 — парсинг HTML.