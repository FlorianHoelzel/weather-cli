import io
import json
import ssl
import unittest
from unittest.mock import patch

from weather import get_coordinates, get_weather


class WeatherRequestTests(unittest.TestCase):
    def test_both_requests_verify_https_with_certifi(self):
        responses = [
            {"results": [{"latitude": 52.52, "longitude": 13.41}]},
            {"current": {
                "temperature_2m": 8.8, "apparent_temperature": 7.2,
                "relative_humidity_2m": 80, "wind_speed_10m": 12.3,
                "weather_code": 3, "is_day": 0, "time": "2026-11-01T20:00",
            }},
        ]
        with (
            patch("weather.urlopen", side_effect=[
                io.StringIO(json.dumps(data)) for data in responses
            ]) as request,
            patch("weather.ssl.create_default_context",
                  wraps=ssl.create_default_context) as create_context,
        ):
            coordinates = get_coordinates("Berlin")
            weather = get_weather(*coordinates)
        self.assertEqual(coordinates, (52.52, 13.41))
        self.assertEqual(weather["temperature"], 8.8)
        self.assertEqual(create_context.call_count, 2)
        for call in create_context.call_args_list:
            self.assertTrue(call.kwargs["cafile"])
        for call in request.call_args_list:
            self.assertTrue(call.args[0].startswith("https://"))
            context = call.kwargs["context"]
            self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
            self.assertTrue(context.check_hostname)


if __name__ == "__main__":
    unittest.main()
