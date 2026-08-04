from urllib.request import Request, urlopen

from PyQt6.QtCore import QThread, pyqtSignal

from src import config


_cache: dict[str, bytes] = {}
_failed: set[str] = set()
_in_flight: dict[str, list] = {}
_active_workers: list = []


class _IconFetchWorker(QThread):
    finished_fetch = pyqtSignal(str, object)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            request = Request(self.url, headers={"User-Agent": config.HTTP_USER_AGENT})
            data = urlopen(request, timeout=config.ICON_FETCH_TIMEOUT_SECONDS).read()
        except Exception:
            data = None
        self.finished_fetch.emit(self.url, data)


def clear_icon_cache() -> None:
    _cache.clear()
    _failed.clear()


def fetch_icon(url: str, callback) -> None:
    if not url:
        callback(None)
        return

    if url in _cache:
        callback(_cache[url])
        return

    if url in _failed:
        callback(None)
        return

    if url in _in_flight:
        _in_flight[url].append(callback)
        return

    _in_flight[url] = [callback]

    worker = _IconFetchWorker(url)
    _active_workers.append(worker)

    def _on_finished(finished_url, data):
        if data is not None:
            _cache[finished_url] = data
        else:
            _failed.add(finished_url)

        callbacks = _in_flight.pop(finished_url, [])
        for cb in callbacks:
            try:
                cb(data)
            except RuntimeError:
                pass

        if worker in _active_workers:
            _active_workers.remove(worker)
        worker.deleteLater()

    worker.finished_fetch.connect(_on_finished)
    worker.start()
