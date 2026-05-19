from __future__ import annotations

import argparse
import errno
import signal
import sys
import time
from pathlib import Path

from .models import Route
from .openapi import import_openapi
from .server import MockServer
from .store import RouteStore
from .tui import Tui
from .watcher import RouteFileWatcher


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Terminal API mock server with a live TUI.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind. Defaults to 127.0.0.1.")
    parser.add_argument("--port", default=8080, type=int, help="Port to bind. Defaults to 8080.")
    parser.add_argument("--file", type=Path, help="Route file to load and save.")
    parser.add_argument("--import-openapi", type=Path, help="Import an OpenAPI JSON file into the route file and exit.")
    parser.add_argument("--headless", action="store_true", help="Run the mock server without the TUI.")
    parser.add_argument("--no-watch", action="store_true", help="Disable automatic reload when the route file changes.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    route_file = args.file or Path("routes.json")
    if args.import_openapi:
        if not args.import_openapi.exists():
            print(f"Termimock OpenAPI file not found: {args.import_openapi}", file=sys.stderr)
            return 1
        store = RouteStore(import_openapi(args.import_openapi))
        store.save(route_file)
        print(f"Imported {len(store.list_routes())} routes into {route_file}")
        return 0

    store = RouteStore()
    if route_file.exists():
        store.load(route_file)
    elif args.file is not None:
        print(f"Termimock route file not found: {route_file}", file=sys.stderr)
        return 1
    else:
        store.add_route(Route("GET", "/api/health", body='{"ok":true}'))

    server = MockServer(store, args.host, args.port, route_file)
    watcher = None
    try:
        server.start()
    except OSError as exc:
        if exc.errno in {errno.EADDRINUSE, 48}:
            print(
                f"Termimock could not start because {args.host}:{args.port} is already in use.\n"
                f"Try another port, for example: termimock --port {args.port + 1}",
                file=sys.stderr,
            )
            return 1
        raise
    if not args.no_watch and route_file.exists():
        watcher = RouteFileWatcher(store, route_file, on_error=lambda exc: print(f"Termimock reload failed: {exc}", file=sys.stderr))
        watcher.start()
    try:
        if args.headless:
            print(f"Termimock listening on {server.address}. GUI: {server.address}/_termimock. Press Ctrl+C to stop.", flush=True)
            _wait_forever()
        else:
            Tui(store, server, route_file).run()
    finally:
        if watcher:
            watcher.stop()
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
