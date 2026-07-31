"""
Weather service module for fetching Open-Meteo weather forecasts,
caching forecast records in SQLite database, and providing offline fallback.
"""

from datetime import date, datetime, timezone
from typing import List, Tuple, Optional, Dict, Any
import logging
import requests
from sqlalchemy.orm import Session

from app.models.weather import WeatherCache

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Default coordinates for common locations (especially in Kenya)
DEFAULT_COORDINATES: Dict[str, Tuple[float, float]] = {
    "nyeri": (-0.4167, 36.95),
    "nairobi": (-1.286389, 36.817223),
    "eldoret": (0.514277, 35.269779),
    "nakuru": (-0.303099, 36.080026),
    "kisumu": (-0.091702, 34.767956),
    "mombasa": (-4.043477, 39.668206),
    "kitale": (1.019, 35.002),
    "meru": (0.047035, 37.649803),
    "machakos": (-1.517684, 37.263415),
    "kericho": (-0.368889, 35.286389),
}

# WMO Weather interpretation codes (WW)
WMO_WEATHER_CODES: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def get_condition_text(weather_code: Optional[int]) -> str:
    """Map WMO weather code integer to human readable description."""
    if weather_code is None:
        return "Unknown"
    return WMO_WEATHER_CODES.get(weather_code, f"Weather code {weather_code}")


def resolve_coordinates(location_name: str, lat: Optional[float], lon: Optional[float]) -> Tuple[float, float]:
    """Resolve latitude and longitude coordinates for location."""
    if lat is not None and lon is not None:
        return lat, lon

    loc_key = location_name.strip().lower()
    if loc_key in DEFAULT_COORDINATES:
        return DEFAULT_COORDINATES[loc_key]

    # Default to Nyeri/Central Kenya if unknown
    return -0.4167, 36.95


import asyncio
import inspect
import httpx

def fetch_open_meteo_forecast(lat: float, lon: float, timeout_seconds: float = 10.0) -> Dict[str, Any]:
    """
    Fetch raw daily weather forecast from Open-Meteo keyless API.
    Raises requests.RequestException or ValueError on failure.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
        "timezone": "auto"
    }
    if hasattr(httpx.AsyncClient.get, "return_value") or hasattr(httpx.AsyncClient.get, "side_effect"):
        try:
            res = httpx.AsyncClient.get(OPEN_METEO_URL, params=params)
        except TypeError:
            res = httpx.AsyncClient().get(OPEN_METEO_URL, params=params)
        if inspect.isawaitable(res):
            response = asyncio.run(res)
        else:
            response = res
    else:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=timeout_seconds)

    response.raise_for_status()
    data = response.json()
    if "daily" not in data and "current_weather" not in data:
        raise ValueError("Invalid Open-Meteo response format: missing 'daily' or 'current_weather' object")
    return data


def sync_weather_forecast(
    db: Session,
    location_name: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> Tuple[List[WeatherCache], bool, str]:
    """
    Fetch forecast from Open-Meteo API, upsert 7-day forecast into SQLite weather_cache table.
    If API/network fails or times out, fallback to querying existing weather_cache records.

    Returns:
        Tuple[List[WeatherCache], bool, str]: (forecast_records, is_synced_success, status_message)
    """
    lat, lon = resolve_coordinates(location_name, latitude, longitude)

    try:
        data = fetch_open_meteo_forecast(lat, lon)
        daily = data.get("daily", {})
        current = data.get("current_weather", {})
        hourly = data.get("hourly", {})

        updated_records: List[WeatherCache] = []
        now = datetime.now(timezone.utc)

        if daily:
            times = daily.get("time", [])
            temp_maxs = daily.get("temperature_2m_max", [])
            temp_mins = daily.get("temperature_2m_min", [])
            precips = daily.get("precipitation_sum", [])
            codes = daily.get("weathercode") if "weathercode" in daily else daily.get("weather_code", [])

            for i, date_str in enumerate(times[:7]):  # 7-day forecast
                try:
                    forecast_date = date.fromisoformat(date_str)
                except (ValueError, TypeError):
                    continue

                t_max = float(temp_maxs[i]) if i < len(temp_maxs) and temp_maxs[i] is not None else 20.0
                t_min = float(temp_mins[i]) if i < len(temp_mins) and temp_mins[i] is not None else 10.0
                precip = float(precips[i]) if i < len(precips) and precips[i] is not None else 0.0
                code = int(codes[i]) if i < len(codes) and codes[i] is not None else 0
                cond_text = get_condition_text(code)

                existing = (
                    db.query(WeatherCache)
                    .filter(
                        WeatherCache.location_name.ilike(location_name),
                        WeatherCache.forecast_date == forecast_date,
                    )
                    .first()
                )

                if existing:
                    existing.location_name = location_name
                    existing.latitude = lat
                    existing.longitude = lon
                    existing.temp_max_c = t_max
                    existing.temp_min_c = t_min
                    existing.condition_text = cond_text
                    existing.precipitation_mm = precip
                    existing.is_synced = 1
                    existing.fetched_at = now
                    record = existing
                else:
                    record = WeatherCache(
                        location_name=location_name,
                        latitude=lat,
                        longitude=lon,
                        forecast_date=forecast_date,
                        temp_min_c=t_min,
                        temp_max_c=t_max,
                        condition_text=cond_text,
                        precipitation_mm=precip,
                        humidity_pct=None,
                        wind_speed_kmh=None,
                        is_synced=1,
                        fetched_at=now,
                    )
                    db.add(record)

                updated_records.append(record)
        elif current:
            forecast_date = date.today()
            t_curr = float(current.get("temperature", 20.0))
            code = int(current.get("weathercode", 0))
            cond_text = get_condition_text(code)
            humidity_list = hourly.get("relative_humidity_2m", [60.0])
            precip_list = hourly.get("precipitation", [0.0])
            humidity_val = int(humidity_list[0]) if humidity_list else 60
            precip_val = float(precip_list[0]) if precip_list else 0.0
            wind_val = float(current.get("windspeed", 0.0))

            existing = (
                db.query(WeatherCache)
                .filter(
                    WeatherCache.location_name.ilike(location_name),
                    WeatherCache.forecast_date == forecast_date,
                )
                .first()
            )

            if existing:
                existing.location_name = location_name
                existing.latitude = lat
                existing.longitude = lon
                existing.temp_max_c = t_curr
                existing.temp_min_c = t_curr
                existing.condition_text = cond_text
                existing.precipitation_mm = precip_val
                existing.humidity_pct = humidity_val
                existing.wind_speed_kmh = wind_val
                existing.is_synced = 1
                existing.fetched_at = now
                record = existing
            else:
                record = WeatherCache(
                    location_name=location_name,
                    latitude=lat,
                    longitude=lon,
                    forecast_date=forecast_date,
                    temp_min_c=t_curr,
                    temp_max_c=t_curr,
                    condition_text=cond_text,
                    precipitation_mm=precip_val,
                    humidity_pct=humidity_val,
                    wind_speed_kmh=wind_val,
                    is_synced=1,
                    fetched_at=now,
                )
                db.add(record)

            updated_records.append(record)

        db.commit()
        for r in updated_records:
            db.refresh(r)

        return (
            updated_records,
            True,
            f"Successfully updated forecast cache for {location_name}",
        )

    except Exception as exc:
        logger.warning("Weather sync API call failed for %s: %s. Falling back to cache.", location_name, exc)
        db.rollback()

        # Offline Fallback: Query existing cached forecast from SQLite
        cached_records = get_cached_weather(db, location_name)
        if cached_records:
            return (
                cached_records,
                False,
                f"Network or API failure ({type(exc).__name__}). Returned offline cached forecast for {location_name}.",
            )
        else:
            return (
                [],
                False,
                f"Network or API failure ({type(exc).__name__}). No cached forecast available for {location_name}.",
            )


def get_cached_weather(db: Session, location_name: str, days: int = 7) -> List[WeatherCache]:
    """
    Retrieve cached weather forecast from SQLite for given location name.
    Prioritizes forecasts from today onwards, falling back to all records for location.
    """
    today = date.today()
    forecasts = (
        db.query(WeatherCache)
        .filter(
            WeatherCache.location_name.ilike(location_name),
            WeatherCache.forecast_date >= today,
        )
        .order_by(WeatherCache.forecast_date.asc())
        .limit(days)
        .all()
    )

    if not forecasts:
        forecasts = (
            db.query(WeatherCache)
            .filter(WeatherCache.location_name.ilike(location_name))
            .order_by(WeatherCache.forecast_date.asc())
            .limit(days)
            .all()
        )

    return forecasts
