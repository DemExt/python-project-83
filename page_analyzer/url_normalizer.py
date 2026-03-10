from urllib.parse import urlparse

def normalize_url(url: str) -> str:
    parsed_url = urlparse(url)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.hostname}"
    return normalized_url

