from __future__ import annotations

import curses
from pathlib import Path

from .models import HTTP_METHODS, Route
from .server import MockServer
from .store import RouteStore


class Tui:
    def __init__(self, store: RouteStore, server: MockServer, route_file: Path) -> None:
        self.store = store
        self.server = server
        self.route_file = route_file
        self.selected = 0
        self.message = "a add  e edit  d delete  c clone  space toggle  s save  r reload  q quit"

    def run(self) -> None:
        curses.wrapper(self._main)

    def _main(self, stdscr: curses.window) -> None:
        curses.curs_set(0)
        stdscr.nodelay(False)
        stdscr.keypad(True)
        while True:
            self._draw(stdscr)
            key = stdscr.getch()
            if key in (ord("q"), 27):
                break
            if key in (curses.KEY_DOWN, ord("j")):
                self._move(1)
            elif key in (curses.KEY_UP, ord("k")):
                self._move(-1)
            elif key == ord("a"):
                self._edit_route(stdscr)
            elif key == ord("e"):
                self._edit_selected(stdscr)
            elif key == ord("d"):
                self._delete_selected()
            elif key == ord("c"):
                self._clone_selected()
            elif key == ord(" "):
                self._toggle_selected()
            elif key == ord("s"):
                self._save()
            elif key == ord("r"):
                self._reload()

    def _draw(self, stdscr: curses.window) -> None:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        title = f"Termimock  {self.server.address}  routes: {self.route_file}"
        self._add(stdscr, 0, 0, title[: width - 1], curses.A_BOLD)
        self._add(stdscr, 1, 0, self.message[: width - 1])
        self._add(stdscr, 3, 0, "Routes", curses.A_BOLD)
        self._add(stdscr, 4, 0, "    METHOD  PATH                         ST  DELAY   VARIANTS  CONTENT TYPE", curses.A_DIM)

        routes = self.store.list_routes()
        route_area_bottom = max(6, height // 2)
        for offset, route in enumerate(routes[: max(0, route_area_bottom - 5)]):
            attr = curses.A_REVERSE if offset == self.selected else curses.A_NORMAL
            self._add(stdscr, 5 + offset, 0, route.label()[: width - 1], attr)

        log_top = route_area_bottom + 1
        self._add(stdscr, log_top, 0, "Requests", curses.A_BOLD)
        self._add(stdscr, log_top + 1, 0, "METHOD  PATH                               ST  MATCH", curses.A_DIM)
        for offset, entry in enumerate(self.store.list_logs()[: max(0, height - log_top - 3)]):
            self._add(stdscr, log_top + 2 + offset, 0, entry.label()[: width - 1])

        stdscr.refresh()

    def _add(self, window: curses.window, y: int, x: int, text: str, attr: int = curses.A_NORMAL) -> None:
        height, width = window.getmaxyx()
        if 0 <= y < height and x < width:
            window.addstr(y, x, text[: max(0, width - x - 1)], attr)

    def _move(self, delta: int) -> None:
        count = len(self.store.list_routes())
        if count:
            self.selected = max(0, min(count - 1, self.selected + delta))

    def _edit_selected(self, stdscr: curses.window) -> None:
        routes = self.store.list_routes()
        if not routes:
            self.message = "No route selected"
            return
        route = self._edit_route(stdscr, routes[self.selected])
        if route:
            self.store.update_route(self.selected, route)

    def _edit_route(self, stdscr: curses.window, route: Route | None = None) -> Route | None:
        existing = route or Route("GET", "/api/example", body='{"ok":true}')
        curses.echo()
        curses.curs_set(1)
        try:
            method = self._prompt(stdscr, "Method", existing.method).upper()
            if method not in HTTP_METHODS:
                self.message = f"Unsupported method: {method}"
                return None
            path = self._prompt(stdscr, "Path", existing.path)
            status = int(self._prompt(stdscr, "Status", str(existing.status)))
            delay_ms = int(self._prompt(stdscr, "Delay ms", str(existing.delay_ms)))
            content_type = self._prompt(stdscr, "Content-Type", existing.content_type)
            headers = dict(existing.headers)
            body = self._prompt(stdscr, "Body", existing.body)
            new_route = Route(method, path, status, content_type, headers, body, existing.enabled, delay_ms, body_match=existing.body_match)
            if route is None:
                self.store.add_route(new_route)
                self.selected = len(self.store.list_routes()) - 1
                self.message = "Route added"
                return None
            self.message = "Route updated"
            return new_route
        except (ValueError, curses.error) as exc:
            self.message = f"Could not save route: {exc}"
            return None
        finally:
            curses.noecho()
            curses.curs_set(0)

    def _prompt(self, stdscr: curses.window, label: str, default: str) -> str:
        height, width = stdscr.getmaxyx()
        prompt = f"{label} [{default}]: "
        stdscr.move(height - 2, 0)
        stdscr.clrtoeol()
        stdscr.addstr(height - 2, 0, prompt[: width - 1], curses.A_BOLD)
        raw = stdscr.getstr(height - 2, min(len(prompt), width - 1), max(1, width - len(prompt) - 1))
        value = raw.decode("utf-8").strip()
        return value or default

    def _delete_selected(self) -> None:
        if self.store.list_routes():
            self.store.delete_route(self.selected)
            self.selected = max(0, self.selected - 1)
            self.message = "Route deleted"

    def _clone_selected(self) -> None:
        routes = self.store.list_routes()
        if routes:
            route = routes[self.selected]
            clone = Route(
                route.method,
                route.path,
                route.status,
                route.content_type,
                route.headers,
                route.body,
                route.enabled,
                route.delay_ms,
                body_match=route.body_match,
            )
            self.store.add_route(clone)
            self.selected = len(self.store.list_routes()) - 1
            self.message = "Route cloned"

    def _toggle_selected(self) -> None:
        routes = self.store.list_routes()
        if routes:
            route = routes[self.selected]
            route.enabled = not route.enabled
            self.store.update_route(self.selected, route)
            self.message = "Route toggled"

    def _save(self) -> None:
        self.store.save(self.route_file)
        self.message = f"Saved {self.route_file}"

    def _reload(self) -> None:
        if self.route_file.exists():
            self.store.load(self.route_file)
            self.selected = 0
            self.message = f"Reloaded {self.route_file}"
        else:
            self.message = f"{self.route_file} does not exist"
