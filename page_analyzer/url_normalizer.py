from urllib.parse import urlparse


def normalize_url(url):
    parsed = urlparse(url)
    # Оставляем ТОЛЬКО схему и домен, переводим в нижний регистр
    # Все остальное (path, params, query, fragment) отбрасываем
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
