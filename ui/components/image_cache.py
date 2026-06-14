from PySide6.QtGui import QPixmap

_cache: dict[str, QPixmap] = {}


def get_cached(url: str) -> QPixmap | None:
    return _cache.get(url)


def store(url: str, data: bytes) -> QPixmap:
    px = QPixmap()
    px.loadFromData(data)
    _cache[url] = px
    return px


def is_cached(url: str) -> bool:
    return url in _cache
