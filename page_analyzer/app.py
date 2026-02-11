import os
import psycopg2
import psycopg2.extras
import validators
import re
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
import datetime
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# Загружаем переменные окружения
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')


# Функция соединения с базой
def get_db_connection():
    return psycopg2.connect(os.getenv('DATABASE_URL'))


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
        return {'status_code': None}
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

        # Поиск совпадений
        matches = find_matches(url_input)

        # Вставка в БД
        con = get_db_connection()
        try:
            with con.cursor() as cur:
                cur.execute(
                    "INSERT INTO urls (name) VALUES (%s) ON "
                    "CONFLICT (name) DO NOTHING RETURNING id",
                    (url_input,)
                )
                inserted = cur.fetchone()
                con.commit()

            if inserted:
                flash('URL успешно добавлен!', 'success')
            else:
                flash('Этот URL уже существует', 'info')

            # Отображение совпадений
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
        with con.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT id, name, created_at FROM "
                        "urls ORDER BY created_at DESC")
            urls = cur.fetchall()
    finally:
        con.close()
    return render_template('urls.html', urls=urls)


@app.route('/urls/<int:url_id>')
def url_detail(url_id):
    con = get_db_connection()
    try:
        with con.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT id, name, created_at FROM"
                        " urls WHERE id=%s", (url_id,))
            url = cur.fetchone()

            # Получаем все проверки этого URL
            cur.execute("SELECT id, status_code, title, h1, "
                        "meta_description, created_at FROM url_checks WHERE"
                        " url_id=%s ORDER BY created_at DESC", (url_id,))
            checks = cur.fetchall()
    finally:
        con.close()

    if not url:
        flash("URL не найден", 'error')
        return redirect(url_for('urls_list'))

    return render_template('url.html', url=url, checks=checks)


@app.route('/urls/<int:id>/checks', methods=['POST'])
def url_check(id):
    con = get_db_connection()
    try:
        with con.cursor() as cur:
            # Получить URL из базы
            cur.execute("SELECT id, name FROM urls WHERE id=%s", (id,))
            url_row = cur.fetchone()
            if not url_row:
                flash("URL не найден", 'error')
                return redirect(url_for('urls_list'))

            url_name = url_row[1]
            created_at = datetime.datetime.now()

            # Выполнить проверку
            try:
                response = requests.get(url_name, timeout=10)
                response.status_code
            except requests.RequestException:
                None

            # Выполнить perform_check для парсинга
            result = perform_check(url_name)

            # Вставка новой проверки
            cur.execute(
                """
                "INSERT INTO url_checks ("
                "url_id, "
                "status_code, "
                "title, "
                "h1, "
                "meta_description, "
                "created_at"
                ") "
                "VALUES (%s, %s, %s, %s, %s, %s) "
                "RETURNING id"
                """,
                (
                    id,
                    result['status_code'],
                    result['title'],
                    result['h1'],
                    result['meta_description'],
                    created_at
                )
            )
            con.commit()
    finally:
        con.close()

    flash('Проверка выполнена', 'success')
    return redirect(url_for('url_detail', url_id=id))


pattern = r'([a-z]{3}):\1'


def find_matches(text):
    return re.findall(pattern, text)


if __name__ == '__main__':
    app.run(debug=True)
    