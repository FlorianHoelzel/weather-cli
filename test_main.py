import contextlib
import io
import socket
import ssl
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from main import connection_error, main


class ConnectionErrorTests(unittest.TestCase):
    def test_expired_certificate_keeps_the_cause_visible(self):
        error = ssl.SSLCertVerificationError(1, "verification failed")
        error.verify_message = "certificate has expired"
        message = connection_error(URLError(error))
        self.assertIn("TLS-Zertifikat", message)
        self.assertIn("certificate has expired", message)

    def test_network_failures_have_distinct_messages(self):
        cases = [
            (URLError(socket.gaierror()), "DNS"),
            (URLError(TimeoutError()), "Zeitüberschreitung"),
            (TimeoutError(), "Zeitüberschreitung"),
            (HTTPError("https://example.com", 429, "Too Many Requests", {}, None), "HTTP 429"),
            (URLError(ssl.SSLError()), "TLS"),
            (URLError(ConnectionRefusedError()), "Firewall"),
        ]
        for error, expected in cases:
            with self.subTest(expected=expected):
                try:
                    self.assertIn(expected, connection_error(error))
                finally:
                    if isinstance(error, HTTPError):
                        error.close()

    def test_once_reports_forecast_failure_and_exits(self):
        output = io.StringIO()
        with (
            patch("sys.argv", ["main.py", "Berlin", "--once"]),
            patch("main.get_coordinates", return_value=(52.52, 13.41)),
            patch("main.get_weather", side_effect=URLError(TimeoutError())),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(main(), 1)
        self.assertIn("Zeitüberschreitung", output.getvalue())
        self.assertIn("konnte nicht geladen werden", output.getvalue())
        self.assertNotIn("wird geladen", output.getvalue())

    def test_geocoding_failure_reports_cause(self):
        output = io.StringIO()
        with (
            patch("sys.argv", ["main.py", "Berlin", "--once"]),
            patch("main.get_coordinates", side_effect=URLError(socket.gaierror())),
            contextlib.redirect_stderr(output),
        ):
            self.assertEqual(main(), 1)
        self.assertIn("Ortssuche fehlgeschlagen", output.getvalue())
        self.assertIn("DNS", output.getvalue())


if __name__ == "__main__":
    unittest.main()
