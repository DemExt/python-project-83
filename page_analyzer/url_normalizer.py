import re
from urllib.parse import urlparse, urlunparse


def normalize_url(url):
    # Добавляем схему по умолчанию if отсутствует
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', url):
        url = 'http://' + url

    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    path = parsed.path

    # Убираем слэш в конце пути, кроме если путь — это корень ('/')
    if path != '/' and path.endswith('/'):
        path = path.rstrip('/')

    # Строим нормализованный URL
    normalized = urlunparse((scheme, netloc, path, '', '', ''))
    return normalized
