from urllib.parse import urlparse


def normalize_url(url):
    parsed = urlparse(url)
    # Схема и домен — в нижний регистр
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    # Путь оставляем, но убираем лишний слеш в конце, если он есть
    path = parsed.path.rstrip('/')
    return f"{scheme}://{netloc}{path}"