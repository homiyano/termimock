import unittest

from termimock.models import Route, RouteResponse, normalize_path


class RouteTests(unittest.TestCase):
    def test_normalizes_path_and_method(self):
        route = Route("get", "api/user")

        self.assertEqual(route.method, "GET")
        self.assertEqual(route.path, "/api/user")

    def test_rejects_unsupported_method(self):
        with self.assertRaises(ValueError):
            Route("BREW", "/coffee")

    def test_validates_status(self):
        with self.assertRaises(ValueError):
            Route("GET", "/", status=99)

    def test_accepts_delay_ms(self):
        route = Route("GET", "/", delay_ms=150)

        self.assertEqual(route.delay_ms, 150)

    def test_accepts_multiple_responses(self):
        route = Route(
            "GET",
            "/",
            responses=[RouteResponse(200, body="ok"), RouteResponse(500, body="no")],
            response_mode="cycle",
        )

        self.assertEqual(len(route.responses), 2)
        self.assertEqual(route.response_mode, "cycle")

    def test_rejects_unknown_response_mode(self):
        with self.assertRaises(ValueError):
            Route("GET", "/", response_mode="shuffle")

    def test_loads_body_match_from_match_json(self):
        route = Route.from_dict({"method": "POST", "path": "/login", "match": {"json": {"email": "ada@example.com"}}})

        self.assertEqual(route.body_match, {"email": "ada@example.com"})

    def test_normalize_path_handles_empty_value(self):
        self.assertEqual(normalize_path(""), "/")


if __name__ == "__main__":
    unittest.main()
