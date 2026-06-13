import requests
from typing import Optional
from config import TMDB_BASE, TMDB_IMG_W500, TMDB_IMG_W1280, TMDB_IMG_ORIG

TIMEOUT = 10


class TMDbClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.params = {"api_key": api_key, "language": "en-US"}

    def get_popular_movies(self, page: int = 1) -> dict:
        return self._get("/movie/popular", {"page": page})

    def get_genres(self) -> dict:
        return self._get("/genre/movie/list")

    def get_movie_detail(self, movie_id: int) -> dict:
        data = self._get(f"/movie/{movie_id}")
        if not data.get("overview", "").strip():
            data = self._get(f"/movie/{movie_id}", {"language": "en-US"})
        return data

    def search_movies(self, query: str, page: int = 1) -> dict:
        return self._get("/search/movie", {"query": query, "page": page})

    def get_trending(self, window: str = "week") -> dict:
        return self._get(f"/trending/movie/{window}")

    def poster_url(self, path: Optional[str], size: str = "w500") -> Optional[str]:
        if not path:
            return None
        base = TMDB_IMG_W500 if size == "w500" else TMDB_IMG_W1280
        return f"{base}{path}"

    def backdrop_url(self, path: Optional[str]) -> Optional[str]:
        if not path:
            return None
        return f"{TMDB_IMG_ORIG}{path}"

    def fetch_image_bytes(self, url: str) -> Optional[bytes]:
        try:
            r = requests.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            return r.content
        except Exception:
            return None

    def _get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{TMDB_BASE}{endpoint}"
        r = self.session.get(url, params=params or {}, timeout=TIMEOUT)
        if r.status_code == 401:
            raise ValueError("API Key tidak valid. Periksa config.py.")
        if r.status_code == 404:
            raise ValueError(f"Endpoint tidak ditemukan: {endpoint}")
        r.raise_for_status()
        return r.json()
