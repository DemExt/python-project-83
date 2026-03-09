import re
from urllib.parse import urlparse

def normalize_url(url):
    # Добавляем http:// если его нет, чтобы validators.url не выдавал 422
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', url):
        url = f'http://{url}'
        
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    # Сохраняем путь (path), но убираем слеш в конце для дублей
    path = parsed.path.rstrip('/')
    return f"{scheme}://{netloc}{path}"
