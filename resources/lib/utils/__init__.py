from urllib.parse import urlencode
import xbmcaddon

BASE_URL = ''

PAGE_SIZES = (20, 40, 60, 100)


def get_url(**kwargs):
    return '{}?{}'.format(BASE_URL, urlencode({k: v for k, v in kwargs.items() if v is not None}))


def page_size() -> int:
    try:
        return PAGE_SIZES[int(xbmcaddon.Addon().getSetting('page_size'))]
    except (ValueError, IndexError):
        return 40


def kodi_datetime(iso: str) -> str:
    """Stash RFC 3339 timestamp (2024-06-29T12:34:56+02:00) to Kodi's 2024-06-29 12:34:56"""
    if not iso:
        return ''
    return iso[:19].replace('T', ' ')
