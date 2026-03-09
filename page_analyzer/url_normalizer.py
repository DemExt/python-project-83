import re
from urllib.parse import urlparse

def normalize_url(url):
    # Добавляем протокол, если пользователь его забыл
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', url):
        url = f'http://{url}'
        
    parsed = urlparse(url)
    # Оставляем ТОЛЬКО схему и домен в нижнем регистре
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
