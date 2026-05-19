from io import StringIO
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import errno

from termimock.cli import main


class CliTests(TestCase):
    def test_reports_busy_port_without_traceback(self):
        with patch("termimock.cli.MockServer.start", side_effect=OSError(errno.EADDRINUSE, "Address already in use")):
            with patch("sys.stderr", new_callable=StringIO) as stderr:
                exit_code = main(["--headless", "--port", "8080"])

        self.assertEqual(exit_code, 1)
        self.assertIn("127.0.0.1:8080 is already in use", stderr.getvalue())
        self.assertIn("termimock --port 8081", stderr.getvalue())

    def test_reports_missing_explicit_route_file(self):
        missing_file = Path("does-not-exist.json")

        with patch("sys.stderr", new_callable=StringIO) as stderr:
            exit_code = main(["--headless", "--file", str(missing_file)])

        self.assertEqual(exit_code, 1)
        self.assertIn("route file not found", stderr.getvalue())
        self.assertIn(str(missing_file), stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
