from __future__ import annotations

from urllib.parse import quote
from urllib.request import urlopen
import json
import ssl

import certifi


def _get_json(url: str) -> dict:
    # Use Mozilla's CA bundle instead of stale certificates in the local store.
    context = ssl.create_default_context(cafile=certifi.where())
    with urlopen(url, timeout=10, context=context) as response:
        return json.load(response)

def get_coordinates(city: str) -> tuple[float, float]:
    url = f'https://geocoding-api.open-meteo.com/v1/search?name={quote(city)}'
    data = _get_json(url)
    results = data.get("results", [])
    if not results:
        raise ValueError("results is empty")
    return results[0]["latitude"], results[0]["longitude"]

def get_weather(latitude: float, longitude: float) -> dict[str, float | int | str]:
    fields = "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code,is_day"
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}"
        f"&current={fields}&timezone=auto&temperature_unit=celsius&wind_speed_unit=kmh"
    )
    data = _get_json(url)
    current = data["current"]
    return {
        "temperature": float(current["temperature_2m"]),
        "feels_like": float(current["apparent_temperature"]),
        "humidity": int(current["relative_humidity_2m"]),
        "wind": float(current["wind_speed_10m"]),
        "code": int(current["weather_code"]),
        "is_day": int(current["is_day"]),
        "time": str(current["time"]),
    }
