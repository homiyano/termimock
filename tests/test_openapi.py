from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from termimock.openapi import import_openapi


class OpenApiTests(unittest.TestCase):
    def test_imports_routes_from_openapi_json(self):
        with TemporaryDirectory() as temp_dir:
            spec_file = Path(temp_dir) / "openapi.json"
            spec_file.write_text(
                """
                {
                  "openapi": "3.0.0",
                  "paths": {
                    "/api/users/{id}": {
                      "get": {
                        "responses": {
                          "200": {
                            "content": {
                              "application/json": {
                                "schema": {
                                  "type": "object",
                                  "properties": {
                                    "id": {"type": "integer"},
                                    "name": {"type": "string"},
                                    "active": {"type": "boolean"}
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
                """,
                encoding="utf-8",
            )

            routes = import_openapi(spec_file)

        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0].method, "GET")
        self.assertEqual(routes[0].path, "/api/users/{id}")
        self.assertEqual(routes[0].body, '{"id":0,"name":"string","active":false}')


if __name__ == "__main__":
    unittest.main()
