"""Free weather forecasts via Open-Meteo (no API key required)."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

structlogger = structlog.get_logger()

_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes (Open-Meteo).
_WMO = {
    0: "clear",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "drizzle",
    55: "heavy drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    80: "light showers",
    81: "showers",
    82: "heavy showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "thunderstorm with heavy hail",
}


def _condition(code: Any) -> str:
    try:
        return _WMO.get(int(code), f"code {code}")
    except (TypeError, ValueError):
        return "unknown"


async def _geocode(place: str) -> dict[str, Any] | None:
    params = {"name": place, "count": 5, "language": "en", "format": "json"}
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(_GEOCODE, params=params)
        response.raise_for_status()
        payload = response.json()
    results = payload.get("results") or []
    if not results:
        return None
    hit = results[0]
    parts = [
        str(hit.get("name") or "").strip(),
        str(hit.get("admin1") or "").strip(),
        str(hit.get("country") or "").strip(),
    ]
    label = ", ".join(part for part in parts if part)
    return {
        "label": label or place,
        "latitude": hit["latitude"],
        "longitude": hit["longitude"],
        "timezone": hit.get("timezone") or "auto",
        "alternatives": [
            ", ".join(
                p
                for p in [
                    str(item.get("name") or "").strip(),
                    str(item.get("admin1") or "").strip(),
                    str(item.get("country") or "").strip(),
                ]
                if p
            )
            for item in results[1:4]
        ],
    }


async def _forecast(
    *,
    latitude: float,
    longitude: float,
    timezone: str,
    days: int,
) -> dict[str, Any]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max,precipitation_sum"
        ),
        "timezone": timezone or "auto",
        "forecast_days": days,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(_FORECAST, params=params)
        response.raise_for_status()
        return response.json()


@tool(
    description=(
        "Get a free multi-day weather forecast for a city/place via "
        "Open-Meteo. Pass place and optional days (1-16, default 7)."
    )
)
async def get_weather_forecast(
    place: str = "",
    days: int = 7,
    context: ToolContext = None,
) -> ToolResult:
    """Return an Open-Meteo forecast for the named place.

    Args:
        place: City or place name (e.g. Munich, Berlin, London).
        days: Number of forecast days (1-16). Use 7 for "this week".
    """
    query = str(place or "").strip()
    if not query:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "missing_place",
                "instruction": "Ask which city or place they mean, then call again.",
            }
        )

    try:
        day_count = int(days)
    except (TypeError, ValueError):
        day_count = 7
    day_count = max(1, min(16, day_count))

    try:
        geo = await _geocode(query)
        if not geo:
            return ToolResult(
                llm_response={
                    "ok": False,
                    "error": "place_not_found",
                    "place": query,
                    "instruction": (
                        "Say you could not find that place and ask them to "
                        "retry with a clearer city name."
                    ),
                }
            )
        raw = await _forecast(
            latitude=float(geo["latitude"]),
            longitude=float(geo["longitude"]),
            timezone=str(geo["timezone"]),
            days=day_count,
        )
    except Exception as error:  # noqa: BLE001
        structlogger.error("fun_weather.failed", error=str(error), place=query)
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "weather_lookup_failed",
                "message": str(error),
                "instruction": "Say the weather service failed; ask them to try again.",
            }
        )

    daily = raw.get("daily") or {}
    dates = daily.get("time") or []
    tmax = daily.get("temperature_2m_max") or []
    tmin = daily.get("temperature_2m_min") or []
    codes = daily.get("weather_code") or []
    rain_chance = daily.get("precipitation_probability_max") or []
    rain_sum = daily.get("precipitation_sum") or []

    days_out: list[dict[str, Any]] = []
    for index, date in enumerate(dates):
        days_out.append(
            {
                "date": date,
                "condition": _condition(codes[index] if index < len(codes) else None),
                "temp_max_c": tmax[index] if index < len(tmax) else None,
                "temp_min_c": tmin[index] if index < len(tmin) else None,
                "precip_probability_max_pct": (
                    rain_chance[index] if index < len(rain_chance) else None
                ),
                "precip_mm": rain_sum[index] if index < len(rain_sum) else None,
            }
        )

    return ToolResult(
        llm_response={
            "ok": True,
            "place": geo["label"],
            "timezone": geo["timezone"],
            "source": "Open-Meteo",
            "source_url": "https://open-meteo.com/",
            "days": days_out,
            "alternatives": geo.get("alternatives") or [],
            "instruction": (
                "Summarize the forecast in a short Slack-friendly message. "
                "Include highs/lows in C, conditions, and rain chance when "
                "useful. Name the resolved place. Mention Open-Meteo as the "
                "source. Do not invent numbers beyond days[]."
            ),
        }
    )
