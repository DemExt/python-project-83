import os
import re
import sqlite3
from datetime import datetime
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

        # Проверка совпадений — предполагаемая функция find_matches
        matches = find_matches(url_input)

        con = get_db_connection()
        try:
            cur = con.cursor()
            # Добавляем URL, уникальность по name
            cur.execute(
                "INSERT OR IGNORE INTO urls (name, created_at) "
                "VALUES (?, datetime('now'))",
                (url_input,)
            )
            con.commit()

            # Получаем id URL
            cur.execute("SELECT id FROM urls WHERE name = ?", (url_input,))
            row = cur.fetchone()

            if row:
                flash('URL успешно добавлен!', 'success')
            else:
                flash('Этот URL уже существует', 'info')

            if matches:
                flash(f'Обнаружены шаблоны: {", ".join(matches)}', 'info')
            else:
                flash('Шаблоны не найдены', 'info')

        except Exception as e:
            flash(f'Ошибка базы данных: {e}', 'error')
        finally:
            con.close()

        return redirect(url_for('urls_list'))

    return render_template('index.html')


# Страница со списком URL
@app.route('/urls')
def urls_list():
    con = get_db_connection()
    try:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT id, name, created_at FROM "
                    "urls ORDER BY datetime(created_at) DESC")
        rows = cur.fetchall()

        urls = []
        for row in rows:
            # Получение последней проверки
            cur.execute(
                "SELECT created_at FROM url_checks WHERE url_id = ? "
                "ORDER BY datetime(created_at) DESC LIMIT 1",
                (row['id'],)
            )
            check = cur.fetchone()
            last_check_time = None
            if check:
                last_check_time = datetime.strptime(check['created_at'],
                                                    '%Y-%m-%d %H:%M:%S')

            urls.append({
                'id': row['id'],
                'name': row['name'],
                'created_at': datetime.strptime(row['created_at'],
                                                '%Y-%m-%d %H:%M:%S'),
                'last_check_time': last_check_time
            })
    finally:
        con.close()

    return render_template('urls.html', urls=urls)


# Детали URL и проверки
@app.route('/urls/<int:url_id>')
def url_detail(url_id):
    con = get_db_connection()
    try:
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # Получение URL
        cur.execute("SELECT id, name, created_at FROM "
                    "urls WHERE id = ?", (url_id,))
        url_row = cur.fetchone()
        if not url_row:
            flash("URL не найден", 'error')
            return redirect(url_for('urls_list'))

        url = {
            'id': url_row['id'],
            'name': url_row['name'],
            'created_at': datetime.strptime(url_row['created_at'],
                                            '%Y-%m-%d %H:%M:%S')
        }

        # Получение проверок
        cur.execute("""
            SELECT id, status_code, title, h1, meta_description, created_at
            FROM url_checks WHERE url_id = ? ORDER BY datetime(created_at) DESC
        """, (url_id,))
        checks_rows = cur.fetchall()

        checks = []
        for row in checks_rows:
            checks.append({
                'id': row['id'],
                'status_code': row['status_code'],
                'title': row['title'],
                'h1': row['h1'],
                'meta_description': row['meta_description'],
                'created_at': datetime.strptime(row['created_at'],
                                                '%Y-%m-%d %H:%M:%S')
            })

    finally:
        con.close()

    return render_template('url.html', url=url, checks=checks)


# Выполнение проверки URL
@app.route('/urls/<int:id>/checks', methods=['POST'])
def url_check(id):
    con = get_db_connection()
    try:
        cur = con.cursor()
        # Получаем URL для проверки
        cur.execute("SELECT id, name FROM urls WHERE id = ?", (id,))
        url_row = cur.fetchone()
        if not url_row:
            flash("URL не найден", 'error')
            return redirect(url_for('urls_list'))

        url_name = url_row['name']

        # Выполняем проверку (ваша логика)
        check_result = perform_check(url_name)

        # Вставляем результат в url_checks
        cur.execute(
            """
            INSERT INTO url_checks (url_id, status_code, title,
            h1, meta_description, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                id,
                check_result.get('status_code'),
                check_result.get('title'),
                check_result.get('h1'),
                check_result.get('meta_description')
            )
        )
        con.commit()

    finally:
        con.close()

    return redirect(url_for('url_detail', url_id=id))
