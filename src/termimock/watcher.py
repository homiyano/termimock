from __future__ import annotations

from pathlib import Path
from threading import Event, Thread
from typing import Callable

from .store import RouteStore


class RouteFileWatcher:
    def __init__(
        self,
        store: RouteStore,
        route_file: Path,
        interval: float = 0.5,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        self.store = store
        self.route_file = route_file
        self.interval = interval
        self.on_error = on_error
        self._stopped = Event()
        self._thread: Thread | None = None
        self._last_mtime = self._mtime()

    def start(self) -> None:
        self._thread = Thread(target=self._watch, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stopped.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _watch(self) -> None:
        while not self._stopped.wait(self.interval):
            current_mtime = self._mtime()
            if current_mtime is None or current_mtime == self._last_mtime:
                continue
            self._last_mtime = current_mtime
            try:
                self.store.load(self.route_file)
            except Exception as exc:
                if self.on_error:
                    self.on_error(exc)

    def _mtime(self) -> float | None:
        try:
            return self.route_file.stat().st_mtime
        except FileNotFoundError:
            return None
