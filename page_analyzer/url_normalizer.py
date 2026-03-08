from urllib.parse import urlparse


def normalize_url(url):
    parsed = urlparse(url)
    # Только схему и хост в нижний регистр, остальное не трогаем!
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path
    return f"{scheme}://{netloc}{path}"
