from urllib.parse import urlparse


def normalize_url(url):
    parsed = urlparse(url)
    # Оставляем ТОЛЬКО схему и netloc (домен)
    # Все остальное (пути /users/1, параметры) УДАЛЯЕМ
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"