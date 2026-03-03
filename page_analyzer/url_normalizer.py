from urllib.parse import urlparse, urlunparse


def normalize_url(url):
    parsed = urlparse(url)
    scheme = parsed.scheme or 'http'
    netloc = parsed.netloc or parsed.path
    path = parsed.path if parsed.scheme else ''
    path = path or '/'  # по умолчанию добавляем '/'
    
    # Приведение к нижнему регистру
    scheme = scheme.lower()
    netloc = netloc.lower()
    
    # Уберем слэш в конце пути, кроме если путь — root ('/')
    if path != '/' and path.endswith('/'):
        path = path.rstrip('/')

    normalized = urlunparse((scheme, netloc, path, '', '', ''))
    return normalized
