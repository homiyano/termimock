from __future__ import annotations

import argparse
import signal
import sys
import time
from pathlib import Path

from .models import Route
from .server import MockServer
from .store import RouteStore
from .tui import Tui


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Terminal API mock server with a live TUI.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind. Defaults to 127.0.0.1.")
    parser.add_argument("--port", default=8080, type=int, help="Port to bind. Defaults to 8080.")
    parser.add_argument("--file", default="routes.json", type=Path, help="Route file to load and save.")
    parser.add_argument("--headless", action="store_true", help="Run the mock server without the TUI.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = RouteStore()
    if args.file.exists():
        store.load(args.file)
    else:
        store.add_route(Route("GET", "/api/health", body='{"ok":true}'))

    server = MockServer(store, args.host, args.port)
    server.start()
    try:
        if args.headless:
            print(f"Termimock listening on {server.address}. Press Ctrl+C to stop.", flush=True)
            _wait_forever()
        else:
            Tui(store, server, args.file).run()
    finally:
        server.stop()
    return 0


def _wait_forever() -> None:
    stopped = False

    def stop(_signum: int, _frame: object) -> None:
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while not stopped:
        time.sleep(0.2)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

