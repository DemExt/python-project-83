import os
import re
from urllib.parse import urlparse

import validators
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from .database import get_db_connection
from .parser import perform_check
from .url_normalizer import normalize_url

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')

pattern = r'([a-z]{3}):\1'


def find_matches(text):
    return re.findall(pattern, text)


# Главная страница
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url_input = request.form['url'].strip()

        # Валидация URL
        if len(url_input) > 255:
            flash("URL не должен превышать 255 символов", 'error')
            return redirect(url_for('index'))

        # Нормализация и проверка URL
        url_input = normalize_url(url_input)

        parsed_url = urlparse(url_input)
        if not (parsed_url.scheme and parsed_url.netloc):
            flash("Некорректный URL", 'error')
            return redirect(url_for('index'))

        if not validators.url(url_input):
            flash("Некорректный URL", 'error')
            return redirect(url_for('index'))

        matches = find_matches(url_input)

        con = get_db_connection()
        try:
            cur = con.cursor()

            # Вставка URL, если нет конфликта, с возвратом id
            cur.execute(
                """
                INSERT INTO urls (name, created_at)
                VALUES (%s, CURRENT_TIMESTAMP)
                ON CONFLICT (name) DO NOTHING
                RETURNING id
                """,
                (url_input,)
            )
            row = cur.fetchone()

            if row:
                url_id = row[0]
                flash('Страница успешно добавлена', 'success')
            else:
                # Если URL уже есть, получить id из базы
                cur.execute("SELECT id FROM urls WHERE name = %s", (url_input,))
                existing_row = cur.fetchone()
                if existing_row:
                    url_id = existing_row[0]
                    flash('Страница уже существует', 'info')
                else:
                    flash('Не удалось получить ID для URL', 'error')
                    return redirect(url_for('index'))

            # Выводим найденные или не найденные шаблоны
            if matches:
                flash(f'Обнаружены шаблоны: {", ".join(matches)}', 'info')
            else:
                flash('Шаблоны не найдены', 'info')

            con.commit()
        except Exception as e:
            flash(f'Ошибка базы данных: {e}', 'error')
            return redirect(url_for('index'))
        finally:
            cur.close()
            con.close()

        # Перенаправление на страницу детализации URL
        return redirect(url_for('url_detail', url_id=url_id))

    return render_template('index.html')


# Страница со списком URL
@app.route('/urls')
def urls_list():
    con = get_db_connection()
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id, name, created_at FROM urls ORDER BY created_at DESC"
        )
        rows = cur.fetchall()

        urls = []
        for row in rows:
            url_id, name, created_at = row

            # Получение последней проверки для URL
            cur.execute(
                """
                SELECT created_at FROM url_checks
                WHERE url_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (url_id,)
            )
            check_row = cur.fetchone()
            last_check_time = check_row[0] if check_row else None

            urls.append({
                'id': url_id,
                'name': name,
                'created_at': created_at,
                'last_check_time': last_check_time
            })
    finally:
        cur.close()
        con.close()

    return render_template('urls.html', urls=urls)


# Детали URL и проверки
@app.route('/urls/<int:url_id>')
def url_detail(url_id):
    con = get_db_connection()
    try:
        cur = con.cursor()

        cur.execute(
            "SELECT id, name, created_at FROM urls WHERE id = %s", (url_id,)
        )
        url_row = cur.fetchone()
        if not url_row:
            flash("URL не найден", 'error')
            return redirect(url_for('urls_list'))

        url = {
            'id': url_row[0],
            'name': url_row[1],
            'created_at': url_row[2],
        }

        cur.execute("""
            SELECT id, status_code, title, h1, description, created_at
            FROM url_checks WHERE url_id = %s ORDER BY created_at DESC
        """, (url_id,))
        checks_rows = cur.fetchall()

        checks = []
        for row in checks_rows:
            checks.append({
                'id': row[0],
                'status_code': row[1],
                'title': row[2],
                'h1': row[3],
                'description': row[4],
                'created_at': row[5],
            })

    finally:
        cur.close()
        con.close()

    return render_template('url.html', url=url, checks=checks)


# Выполнение проверки URL
@app.route('/urls/<int:id>/checks', methods=['POST'])
def url_check(id):
    con = get_db_connection()
    try:
        cur = con.cursor()

        cur.execute("SELECT id, name FROM urls WHERE id = %s", (id,))
        url_row = cur.fetchone()
        if not url_row:
            flash("URL не найден", 'error')
            return redirect(url_for('urls_list'))

        url_name = url_row[1]

        check_result = perform_check(url_name)

        cur.execute(
            """
            INSERT INTO url_checks (url_id, status_code, title, h1, description, created_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (
                id,
                check_result.get('status_code'),
                check_result.get('title'),
                check_result.get('h1'),
                check_result.get('description')  # раньше meta_description, теперь description
            )
        )
        con.commit()

    finally:
        cur.close()
        con.close()

    return redirect(url_for('url_detail', url_id=id))