import os
import sqlite3
import validators
import re
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# Загружаем переменные окружения
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')


# Функция соединения с базой
def get_db_connection():
    conn = sqlite3.connect(os.getenv('SQLALCHEMY_DATABASE_URI', 'db.sqlite3'))
    conn.row_factory = sqlite3.Row  # Чтобы возвращать словари вместо кортежей
    return conn

def perform_check(url):
    """
    Загружает страницу по URL, парсит HTML и ищет теги:
    <title>, <h1>, <meta name="description" content="">
    """
    result = {
        'status_code': None,
        'title': None,
        'h1': None,
        'meta_description': None,
    }
    try:
        response = requests.get(url, timeout=10)
        result['status_code'] = response.status_code
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        # Поиск <title>
        title_tag = soup.find('title')
        if title_tag:
            result['title'] = title_tag.get_text(strip=True)
        # Поиск <h1>
        h1_tag = soup.find('h1')
        if h1_tag:
            result['h1'] = h1_tag.get_text(strip=True)
        # Поиск <meta name="description" content="">
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            result['meta_description'] = meta_desc['content'].strip()
    except requests.RequestException:
        return result
    return result


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url_input = request.form['url'].strip()

        # Валидация URL
        if len(url_input) > 255:
            flash("URL не должен превышать 255 символов", 'error')
            return redirect(url_for('index'))

        parsed_url = urlparse(url_input)
        if not (parsed_url.scheme and parsed_url.netloc):
            flash("Некорректный URL", 'error')
            return redirect(url_for('index'))

        if not validators.url(url_input):
            flash("Некорректный URL", 'error')
            return redirect(url_for('index'))

        # Поиск совпадений, функция find_matches должна быть реализована отдельно
        matches = find_matches(url_input)

        con = get_db_connection()
        try:
            cur = con.cursor()
            # В SQLite ON CONFLICT доступен с версии 3.24.0 (UPSERT)
            # Чтобы использовать UPSERT, нужно добавить "ON CONFLICT(name) DO NOTHING"
            cur.execute(
                "INSERT INTO urls (name, created_at) VALUES (?, datetime('now')) "
                "ON CONFLICT(name) DO NOTHING"
                , (url_input,))
            con.commit()

            # Проверяем было ли добавлено
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


@app.route('/urls')
def urls_list():
    con = get_db_connection()
    try:
        con.row_factory = sqlite3.Row  # чтобы получать словари, а не кортежи
        cur = con.cursor()
        cur.execute("SELECT id, name, created_at FROM urls ORDER BY datetime(created_at) DESC")
        rows = cur.fetchall()
        
        urls = []
        for row in rows:
            urls.append({
                'id': row['id'],
                'name': row['name'],
                'created_at': datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
            })
    finally:
        con.close()
    return render_template('urls.html', urls=urls)


@app.route('/urls/<int:url_id>')
def url_detail(url_id):
    con = get_db_connection()
    try:
        con.row_factory = sqlite3.Row  # вернуть строки как словари (Row-подобные)
        cur = con.cursor()

        cur.execute("SELECT id, name, created_at FROM urls WHERE id = ?", (url_id,))
        url_row = cur.fetchone()

        if not url_row:
            flash("URL не найден", 'error')
            return redirect(url_for('urls_list'))

        # Преобразуем Row в обычный словарь и дату в datetime
        url = dict(url_row)
        url['created_at'] = datetime.strptime(url['created_at'], '%Y-%m-%d %H:%M:%S')

        cur.execute("""
            SELECT id, status_code, title, h1, meta_description, created_at 
            FROM url_checks WHERE url_id = ? ORDER BY datetime(created_at) DESC
        """, (url_id,))
        checks_rows = cur.fetchall()

        # Преобразовываем каждый Row в словарь
        checks = []
        for row in checks_rows:
            check = dict(row)
            check['created_at'] = datetime.strptime(check['created_at'], '%Y-%m-%d %H:%M:%S')
            checks.append(check)

    finally:
        con.close()

    return render_template('url.html', url=url, checks=checks)


@app.route('/urls/<int:id>/checks', methods=['POST'])
def url_check(id):
    con = get_db_connection()
    try:
        cur = con.cursor()
        cur.execute("SELECT id, name FROM urls WHERE id = ?", (id,))
        url_row = cur.fetchone()
        if not url_row:
            flash("URL не найден", 'error')
            return redirect(url_for('urls_list'))

        url_name = url_row['name']

        # Выполняем проверку сайта и получаем данные
        check_result = perform_check(url_name)

        # Вставляем результаты проверки
        cur.execute("""
            INSERT INTO url_checks
            (url_id, status_code, title, h1, meta_description, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (id,
              check_result['status_code'],
              check_result['title'],
              check_result['h1'],
              check_result['meta_description']))
        con.commit()

        flash("Проверка сайта выполнена", "success")
    except Exception as e:
        flash(f"Ошибка базы данных: {e}", 'error')
    finally:
        con.close()

    return redirect(url_for('url_detail', url_id=id))

pattern = r'([a-z]{3}):\1'


def find_matches(text):
    return re.findall(pattern, text)


if __name__ == '__main__':
    app.run(debug=True)
