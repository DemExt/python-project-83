from urllib.parse import urlparse, urlunparse


def normalize_url(url):
    parsed = urlparse(url)
    scheme = parsed.scheme or 'http'
    netloc = parsed.netloc or parsed.path
    path = parsed.path if parsed.scheme else ''
    normalized = urlunparse((scheme, netloc, path, '', '', ''))
    return normalized
