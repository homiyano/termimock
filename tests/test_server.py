from http.client import HTTPConnection
import time
import unittest

from termimock.models import Route
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

    def request(self, method, path):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=2)
        conn.request(method, path)
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
