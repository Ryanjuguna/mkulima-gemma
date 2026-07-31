"""
Unit tests for Weather Sync Service and API endpoints.
Uses unittest.mock to mock external Open-Meteo HTTP API calls.
"""

from datetime import date, timedelta
from unittest.mock import patch, MagicMock
import pytest
import requests

from app.models.weather import WeatherCache
from app.services.weather_service import (
    get_condition_text,
    resolve_coordinates,
    sync_weather_forecast,
    get_cached_weather,
)


def make_mock_open_meteo_response(start_date=None, num_days=7):
    """Helper function to generate mock Open-Meteo API response JSON."""
    if start_date is None:
        start_date = date.today()

    dates = [(start_date + timedelta(days=i)).isoformat() for i in range(num_days)]
    return {
        "latitude": -0.4167,
        "longitude": 36.95,
        "timezone": "Africa/Nairobi",
        "daily": {
            "time": dates,
            "temperature_2m_max": [22.5 + i for i in range(num_days)],
            "temperature_2m_min": [13.0 + i for i in range(num_days)],
            "precipitation_sum": [1.5 if i % 2 == 0 else 0.0 for i in range(num_days)],
            "weathercode": [0, 1, 2, 3, 61, 63, 80][:num_days],
        },
    }


def test_wmo_code_mapping():
    """Verify WMO weather codes map to expected descriptive strings."""
    assert get_condition_text(0) == "Clear sky"
    assert get_condition_text(2) == "Partly cloudy"
    assert get_condition_text(61) == "Slight rain"
    assert get_condition_text(95) == "Thunderstorm"
    assert get_condition_text(None) == "Unknown"
    assert get_condition_text(9999) == "Weather code 9999"


def test_resolve_coordinates():
    """Verify coordinate resolution logic."""
    lat, lon = resolve_coordinates("Nyeri", None, None)
    assert lat == -0.4167
    assert lon == 36.95

    lat, lon = resolve_coordinates("CustomLoc", 1.23, 4.56)
    assert lat == 1.23
    assert lon == 4.56

    lat, lon = resolve_coordinates("UnknownLoc", None, None)
    assert lat == -0.4167
    assert lon == 36.95


@patch("app.services.weather_service.requests.get")
def test_sync_weather_api_success(mock_get, client, db_session):
    """Test successful Open-Meteo sync via POST /api/v1/weather/sync."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = make_mock_open_meteo_response()
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    payload = {
        "location_name": "Nyeri",
        "latitude": -0.4167,
        "longitude": 36.95,
    }

    res = client.post("/api/v1/weather/sync", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["synced"] is True
    assert data["updated_records"] == 7
    assert len(data["forecasts"]) == 7

    first_fc = data["forecasts"][0]
    assert first_fc["location_name"] == "Nyeri"
    assert first_fc["temp_max_c"] == 22.5
    assert first_fc["temp_min_c"] == 13.0
    assert first_fc["condition_text"] == "Clear sky"

    # Check database records
    cached = db_session.query(WeatherCache).filter(WeatherCache.location_name == "Nyeri").all()
    assert len(cached) == 7


@patch("app.services.weather_service.requests.get")
def test_sync_weather_upsert_existing(mock_get, client, db_session):
    """Test upserting existing forecast records on consecutive syncs."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = make_mock_open_meteo_response()
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    payload = {"location_name": "Eldoret", "latitude": 0.514, "longitude": 35.27}

    # First sync
    res1 = client.post("/api/v1/weather/sync", json=payload)
    assert res1.status_code == 200
    assert res1.json()["updated_records"] == 7

    # Second sync with updated mock temps
    updated_mock = make_mock_open_meteo_response()
    updated_mock["daily"]["temperature_2m_max"][0] = 30.0
    mock_resp.json.return_value = updated_mock

    res2 = client.post("/api/v1/weather/sync", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["updated_records"] == 7
    assert data2["forecasts"][0]["temp_max_c"] == 30.0

    # Ensure count in DB is still 7, not 14
    cached = db_session.query(WeatherCache).filter(WeatherCache.location_name == "Eldoret").all()
    assert len(cached) == 7


@patch("app.services.weather_service.requests.get")
def test_sync_weather_offline_fallback_with_cache(mock_get, client, db_session):
    """Test offline fallback when network request raises exception but cache exists."""
    # Step 1: Pre-populate cache
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = make_mock_open_meteo_response()
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    payload = {"location_name": "Nakuru"}
    client.post("/api/v1/weather/sync", json=payload)

    # Step 2: Simulate network failure / timeout
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

    res = client.post("/api/v1/weather/sync", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["synced"] is False
    assert "Returned offline cached forecast" in data["message"]
    assert data["updated_records"] == 7
    assert len(data["forecasts"]) == 7


@patch("app.services.weather_service.requests.get")
def test_sync_weather_offline_fallback_no_cache(mock_get, client):
    """Test offline fallback when network fails and no cached data exists."""
    mock_get.side_effect = requests.exceptions.ConnectionError("No network connection")

    payload = {"location_name": "UnknownVillage"}
    res = client.post("/api/v1/weather/sync", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["synced"] is False
    assert "No cached forecast available" in data["message"]
    assert data["updated_records"] == 0
    assert data["forecasts"] == []


@patch("app.services.weather_service.requests.get")
def test_get_cached_weather_endpoint(mock_get, client):
    """Test GET /api/v1/weather endpoint."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = make_mock_open_meteo_response()
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    # Sync first
    client.post("/api/v1/weather/sync", json={"location_name": "Mombasa"})

    # GET request
    get_res = client.get("/api/v1/weather?location_name=Mombasa&days=5")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["location"] == "Mombasa"
    assert len(data["cached_forecasts"]) == 5


@patch("app.services.weather_service.requests.get")
def test_legacy_weather_aliases(mock_get, client):
    """Test /api/weather and /api/weather/sync legacy route aliases."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = make_mock_open_meteo_response()
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    sync_res = client.post("/api/weather/sync", json={"location_name": "Kisumu"})
    assert sync_res.status_code == 200

    get_res = client.get("/api/weather?location_name=Kisumu")
    assert get_res.status_code == 200
    assert get_res.json()["location"] == "Kisumu"
    assert len(get_res.json()["cached_forecasts"]) == 7
