import requests
from PySide6.QtCore import QThread, Signal


class _BaseWorker(QThread):

    def __init__(self):
        super().__init__()
        self._stopped = False

    def stop(self):
        self._stopped = True
        self.quit()
        self.wait(2000)   


class MovieFetchWorker(_BaseWorker):
    finished = Signal(list)
    progress = Signal(int, int)
    error    = Signal(str)

    def __init__(self, client, pages: int = 3):
        super().__init__()
        self.client = client
        self.pages  = pages

    def run(self):
        try:
            results, seen = [], set()
            for p in range(1, self.pages + 1):
                if self._stopped:
                    return
                data = self.client.get_popular_movies(page=p)
                for f in data.get("results", []):
                    if f.get("id") not in seen:
                        seen.add(f["id"])
                        results.append(f)
                self.progress.emit(p, self.pages)
            if not self._stopped:
                self.finished.emit(results)
        except requests.exceptions.ConnectionError:
            if not self._stopped:
                self.error.emit(
                    "Tidak dapat terhubung ke internet.\n"
                    "Periksa koneksi jaringan Anda."
                )
        except requests.exceptions.Timeout:
            if not self._stopped:
                self.error.emit("Server TMDb tidak merespons.\nCoba lagi nanti.")
        except ValueError as e:
            if not self._stopped:
                self.error.emit(str(e))
        except Exception as e:
            if not self._stopped:
                self.error.emit(f"Error tidak terduga: {e}")


class ImageWorker(_BaseWorker):
    finished = Signal(str, bytes)
    failed   = Signal(str)

    def __init__(self, client, url: str):
        super().__init__()
        self.client = client
        self.url    = url

    def run(self):
        if self._stopped:
            return
        data = self.client.fetch_image_bytes(self.url)
        if self._stopped:
            return
        if data:
            self.finished.emit(self.url, data)
        else:
            self.failed.emit(self.url)


class DetailWorker(_BaseWorker):
    finished = Signal(dict)
    error    = Signal(str)

    def __init__(self, client, movie_id: int):
        super().__init__()
        self.client   = client
        self.movie_id = movie_id

    def run(self):
        if self._stopped:
            return
        try:
            result = self.client.get_movie_detail(self.movie_id)
            if not self._stopped:
                self.finished.emit(result)
        except Exception as e:
            if not self._stopped:
                self.error.emit(str(e))


class SearchWorker(_BaseWorker):
    finished = Signal(list)
    error    = Signal(str)

    def __init__(self, client, query: str):
        super().__init__()
        self.client = client
        self.query  = query

    def run(self):
        if self._stopped:
            return
        try:
            data = self.client.search_movies(self.query)
            if not self._stopped:
                self.finished.emit(data.get("results", []))
        except Exception as e:
            if not self._stopped:
                self.error.emit(str(e))
