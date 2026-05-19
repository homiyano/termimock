from http.client import HTTPConnection
import json
import time
import unittest

from termimock.models import Route, RouteResponse
from termimock.server import MockServer
from termimock.store import RouteStore


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.store = RouteStore([Route("GET", "/api/user", status=202, body='{"name":"Ada"}')])
        self.server = MockServer(self.store, "127.0.0.1", 0)
        self.server.start()
        _host, self.port = self.server._httpd.server_address

    def tearDown(self):
        self.server.stop()

    def request(self, method, path, json_body=None):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=2)
        body = None
        headers = {}
        if json_body is not None:
            body = json.dumps(json_body)
            headers["Content-Type"] = "application/json"
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        conn.close()
        return response, body

    def test_serves_matching_route(self):
        response, body = self.request("GET", "/api/user")

        self.assertEqual(response.status, 202)
        self.assertEqual(response.getheader("Content-Type"), "application/json")
        self.assertEqual(body, '{"name":"Ada"}')

    def test_logs_miss(self):
        response, _body = self.request("GET", "/missing")

        self.assertEqual(response.status, 404)
        self.assertEqual(self.wait_for_log().matched, False)

    def test_disabled_route_does_not_match(self):
        route = self.store.list_routes()[0]
        route.enabled = False
        self.store.update_route(0, route)

        response, _body = self.request("GET", "/api/user")

        self.assertEqual(response.status, 404)

    def test_serves_route_with_path_params(self):
        self.store.add_route(Route("GET", "/api/users/:id", body='{"id":"{{params.id}}"}'))

        response, body = self.request("GET", "/api/users/42")

        self.assertEqual(response.status, 200)
        self.assertEqual(body, '{"id":"42"}')

    def test_serves_route_with_braced_path_params(self):
        self.store.add_route(Route("GET", "/api/teams/{team_id}", body='{"team":"{{params.team_id}}"}'))

        response, body = self.request("GET", "/api/teams/design")

        self.assertEqual(response.status, 200)
        self.assertEqual(body, '{"team":"design"}')

    def test_renders_query_templates(self):
        self.store.add_route(Route("GET", "/api/search", body='{"q":"{{query.q}}","path":"{{path}}"}'))

        response, body = self.request("GET", "/api/search?q=mock")

        self.assertEqual(response.status, 200)
        self.assertEqual(body, '{"q":"mock","path":"/api/search"}')

    def test_applies_route_delay(self):
        self.store.add_route(Route("GET", "/api/slow", body='{"slow":true}', delay_ms=50))

        start = time.monotonic()
        response, _body = self.request("GET", "/api/slow")

        self.assertEqual(response.status, 200)
        self.assertGreaterEqual(time.monotonic() - start, 0.04)

    def test_cycles_multiple_responses(self):
        self.store.add_route(
            Route(
                "GET",
                "/api/flaky",
                responses=[
                    RouteResponse(200, body='{"ok":true}'),
                    RouteResponse(500, body='{"ok":false}'),
                ],
                response_mode="cycle",
            )
        )

        first_response, first_body = self.request("GET", "/api/flaky")
        second_response, second_body = self.request("GET", "/api/flaky")
        third_response, third_body = self.request("GET", "/api/flaky")

        self.assertEqual(first_response.status, 200)
        self.assertEqual(first_body, '{"ok":true}')
        self.assertEqual(second_response.status, 500)
        self.assertEqual(second_body, '{"ok":false}')
        self.assertEqual(third_response.status, 200)
        self.assertEqual(third_body, '{"ok":true}')

    def test_matches_json_request_body(self):
        self.store.add_route(
            Route(
                "POST",
                "/api/login",
                status=200,
                body='{"token":"dev-token","email":"{{body.email}}"}',
                body_match={"email": "admin@test.com"},
            )
        )

        response, body = self.request("POST", "/api/login", {"email": "admin@test.com"})

        self.assertEqual(response.status, 200)
        self.assertEqual(body, '{"token":"dev-token","email":"admin@test.com"}')

    def test_rejects_unmatched_json_request_body(self):
        self.store.add_route(Route("POST", "/api/login", status=200, body_match={"email": "admin@test.com"}))

        response, _body = self.request("POST", "/api/login", {"email": "user@test.com"})

        self.assertEqual(response.status, 404)

    def test_matches_dotted_json_request_body(self):
        self.store.add_route(
            Route(
                "POST",
                "/api/session",
                status=200,
                body='{"email":"{{body.user.email}}"}',
                body_match={"user.email": "admin@test.com"},
            )
        )

        response, body = self.request("POST", "/api/session", {"user": {"email": "admin@test.com"}})

        self.assertEqual(response.status, 200)
        self.assertEqual(body, '{"email":"admin@test.com"}')

    def test_serves_gui_page(self):
        response, body = self.request("GET", "/_termimock")

        self.assertEqual(response.status, 200)
        self.assertIn("<title>Termimock</title>", body)

    def test_serves_gui_routes_api(self):
        response, body = self.request("GET", "/_termimock/api/routes")

        self.assertEqual(response.status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["routes"][0]["path"], "/api/user")

    def test_saves_routes_from_gui_api(self):
        response, body = self.request(
            "POST",
            "/_termimock/api/routes",
            {"routes": [{"method": "GET", "path": "/api/gui", "body": "{\"gui\":true}"}]},
        )

        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(body)["routes"][0]["path"], "/api/gui")
        response, body = self.request("GET", "/api/gui")
        self.assertEqual(response.status, 200)
        self.assertEqual(body, '{"gui":true}')

    def wait_for_log(self):
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            logs = self.store.list_logs()
            if logs:
                return logs[0]
            time.sleep(0.01)
        self.fail("Timed out waiting for request log entry")


if __name__ == "__main__":
    unittest.main()
