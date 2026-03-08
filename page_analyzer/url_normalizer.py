from urllib.parse import urlparse


def normalize_url(url):
    parsed = urlparse(url)
    # Оставляем только протокол и домен, переводим в нижний регистр
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
