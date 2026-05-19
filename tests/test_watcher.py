from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest

from termimock.models import Route
from termimock.store import RouteStore
from termimock.watcher import RouteFileWatcher


class RouteFileWatcherTests(unittest.TestCase):
    def test_reloads_when_route_file_changes(self):
        with TemporaryDirectory() as temp_dir:
            route_file = Path(temp_dir) / "routes.json"
            route_file.write_text(
                '{"routes":[{"method":"GET","path":"/first","body":"first"}]}',
                encoding="utf-8",
            )
            store = RouteStore([Route("GET", "/initial")])
            store.load(route_file)
            watcher = RouteFileWatcher(store, route_file, interval=0.05)
            watcher.start()
            try:
                time.sleep(0.06)
                route_file.write_text(
                    '{"routes":[{"method":"GET","path":"/second","body":"second"}]}',
                    encoding="utf-8",
                )
                deadline = time.monotonic() + 1
                while time.monotonic() < deadline:
                    if store.list_routes()[0].path == "/second":
                        break
                    time.sleep(0.02)
                self.assertEqual(store.list_routes()[0].path, "/second")
            finally:
                watcher.stop()


if __name__ == "__main__":
    unittest.main()
