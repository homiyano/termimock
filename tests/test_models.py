import unittest

from termimock.models import Route, normalize_path


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

    def test_normalize_path_handles_empty_value(self):
        self.assertEqual(normalize_path(""), "/")


if __name__ == "__main__":
    unittest.main()

