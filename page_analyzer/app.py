import os
import psycopg2
import psycopg2.extras
import validators
import re
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import datetime
from urllib.parse import urlparse
from selenium import webdriver
import requests
from bs4 import BeautifulSoup
from .models import Check

def get_db_connection():
    con = psycopg2.connect(os.getenv('DATABASE_URL'))
    return con

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')

def perform_check(url_obj):
    """
    Загружает страницу по URL, парсит HTML и ищет теги:
    <title>, <h1>, и <meta name="description" content="">
    
    Возвращает словарь:
    {
        'status_code': int или None,  # код ответа или None при ошибке
        'title': str или None,
        'h1': str или None,
        'meta_description': str или None
    }
    """
    result = {
        'status_code': None,
        'title': None,
        'h1': None,
        'meta_description': None,
    }
    
    try:
        response = requests.get(url_obj.name, timeout=10)
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
        # В случае ошибки ничего не делаем, результат останется с None или кодом ошибки
        return {'status_code': None}
    
    return result

@app.route('/urls/<int:id>/checks', methods=['POST'])
def check_url(id):
    session = SessionLocal()
    url_obj = session.query(Url).get(id)
    if not url_obj:
        flash('Сайт не найден', 'danger')
        session.close()
        return redirect(url_for('urls_list'))
    
    try:
        response = requests.get(url_obj.name, timeout=10)
        status_code = response.status_code
        error = None
    except requests.RequestException as e:
        status_code = None
        error = str(e)
        
    result = perform_check(url_obj)

    check = Check(
        url_id=id,
        status_code=result['status_code'] if result['status_code'] is not None else 0,
        title=result['title'],
        h1=result['h1'],
        meta_description=result['meta_description']
    )
    if result['status_code'] is None:
        flash('Произошла ошибка при проверке', 'warning')
    else:
        flash('Проверка выполнена', 'success')

    session.add(check)
    session.commit()
    session.close()

    return redirect(url_for('url_detail', id=id))

# Подключение к базе данных
def get_db_connection():
    return psycopg2.connect(os.getenv('DATABASE_URL'))

# Регулярное выражение для поиска шаблона: трех букв a-z, двоеточие, те же три буквы
pattern = r'([a-z]{3}):\1'

def find_matches(text):
    matches = re.findall(pattern, text)
    return matches

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

        # Поиск совпадений в URL или любом другом тексте
        matches = find_matches(url_input)

        # Вставка в БД
        try:
            con = get_db_connection()
            cur = con.cursor()
            cur.execute(
                "INSERT INTO urls (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING id",
                (url_input,)
            )
            inserted = cur.fetchone()
            con.commit()
            cur.close()
            con.close()

            if inserted:
                flash('URL успешно добавлен!', 'success')
            else:
                flash('Этот URL уже существует', 'info')

            # Вывод совпадений для теста
            if matches:
                flash(f'Обнаружены шаблоны: {", ".join(matches)}', 'info')
            else:
                flash('Шаблоны не найдены', 'info')

            return redirect(url_for('urls_list'))
        except Exception as e:
            flash(f'Ошибка базы данных: {e}', 'error')
            return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/urls')
def urls_list():
    con = get_db_connection()
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id, name, created_at FROM urls ORDER BY created_at DESC")
    urls = cur.fetchall()
    cur.close()
    con.close()
    return render_template('urls.html', urls=urls)

@app.route('/urls/<int:url_id>')
def url_detail(url_id):
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT id, name, created_at FROM urls WHERE id=%s", (url_id,))
    url = cur.fetchone()
    cur.close()
    con.close()

    if not url:
        flash("URL не найден", 'error')
        return redirect(url_for('urls_list'))

    return render_template('url.html', url=url)

@app.route('/urls/<int:id>/checks', methods=['POST'])
def url_check(id):
    try:
        con = get_db_connection()
        cur = con.cursor()
        created_at = datetime.datetime.now()

        # Вставляем новую запись
        cur.execute(
            """
            INSERT INTO url_checks (url_id, created_at)
            VALUES (%s, %s)
            RETURNING id, created_at
            """,
            (id, created_at)
        )
        new_check = cur.fetchone()
        con.commit()
        cur.close()
        con.close()

        return jsonify({
            "id": new_check[0],
            "created_at": new_check[1].isoformat()
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)