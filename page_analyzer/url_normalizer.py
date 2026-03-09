import re
from urllib.parse import urlparse

def normalize_url(url):
    # Если протокола нет (например, 'google.com'), добавляем его
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', url):
        url = f'http://{url}'
    
    parsed = urlparse(url)
    # Возвращаем строго: схема://домен (нижний регистр)
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
