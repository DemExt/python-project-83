import os
import psycopg2
import validators
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from urllib.parse import urlparse

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')

# Подключение к базе данных
def get_db_connection():
    return psycopg2.connect(os.getenv('DATABASE_URL'))

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

            return redirect(url_for('urls_list'))
        except Exception as e:
            flash(f'Ошибка базы данных: {e}', 'error')
            return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/urls')
def urls_list():
    con = get_db_connection()
    cur = con.cursor()
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

if __name__ == '__main__':
    app.run(debug=True)