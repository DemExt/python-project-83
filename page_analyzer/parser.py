import requests
from bs4 import BeautifulSoup


def perform_check(url):
    result = {
        'status_code': None,
        'title': None,
        'h1': None,
        'description': None,
    }
    try:
        response = requests.get(url, timeout=10)
        result['status_code'] = response.status_code
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        title_tag = soup.find('title')
        if title_tag:
            result['title'] = title_tag.get_text(strip=True)

        h1_tag = soup.find('h1')
        if h1_tag:
            result['h1'] = h1_tag.get_text(strip=True)

        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            result['description'] = meta_desc['content'].strip()

    except requests.RequestException:
        # Можно логировать ошибку
        pass
    return result
