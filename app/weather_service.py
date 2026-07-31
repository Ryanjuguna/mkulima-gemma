"""
Compatibility alias for weather service.
"""

from app.services.weather_service import (
    sync_weather_forecast,
    fetch_open_meteo_forecast,
    get_cached_weather,
    get_condition_text,
    resolve_coordinates,
)

# Aliases for alternative import names
sync_weather = sync_weather_forecast
fetch_weather_from_open_meteo = fetch_open_meteo_forecast
