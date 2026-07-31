from unittest.mock import patch, MagicMock
from datetime import date, timedelta


def make_mock_open_meteo_response(num_days=7):
    start_date = date.today()
    dates = [(start_date + timedelta(days=i)).isoformat() for i in range(num_days)]
    return {
        "latitude": -0.4167,
        "longitude": 36.95,
        "timezone": "Africa/Nairobi",
        "daily": {
            "time": dates,
            "temperature_2m_max": [23.0 + i for i in range(num_days)],
            "temperature_2m_min": [14.0 + i for i in range(num_days)],
            "precipitation_sum": [0.0 for _ in range(num_days)],
            "weathercode": [0 for _ in range(num_days)],
        },
    }


@patch("app.services.weather_service.requests.get")
def test_weather_sync_and_get(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = make_mock_open_meteo_response()
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    # Sync weather forecast for Nyeri
    sync_payload = {
        "location_name": "Nyeri",
        "latitude": -0.4167,
        "longitude": 36.95
    }
    sync_res = client.post("/api/v1/weather/sync", json=sync_payload)
    assert sync_res.status_code == 200
    sync_data = sync_res.json()
    assert sync_data["synced"] is True
    assert sync_data["updated_records"] == 7
    assert len(sync_data["forecasts"]) == 7

    # GET cached weather
    get_res = client.get("/api/v1/weather?location_name=Nyeri&days=5")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["location"] == "Nyeri"
    assert len(get_data["cached_forecasts"]) == 5


@patch("app.services.weather_service.requests.get")
def test_legacy_weather_route(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = make_mock_open_meteo_response()
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    sync_payload = {"location_name": "Eldoret"}
    client.post("/api/v1/weather/sync", json=sync_payload)

    res = client.get("/api/weather?location_name=Eldoret")
    assert res.status_code == 200
    assert res.json()["location"] == "Eldoret"
