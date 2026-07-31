import sys
from pathlib import Path
from sqlalchemy import inspect, create_engine

# Add current directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import Base, init_db
from app.main import app
from fastapi.testclient import TestClient


def run_verification():
    print("==================================================")
    print("   MKULIMA GEMMA BACKEND VERIFICATION SUITE       ")
    print("==================================================")

    # 1. Database Table Verification
    print("\n[Step 1] Initializing SQLite database and checking tables...")
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    init_db(target_engine=test_engine)

    inspector = inspect(test_engine)
    created_tables = inspector.get_table_names()
    required_tables = [
        "farmer_activity_logs",
        "weather_cache",
        "pest_disease_history",
        "extension_directory",
    ]

    for table in required_tables:
        assert table in created_tables, f"Missing table: {table}"
        print(f"  [OK] Table '{table}' verified.")

    # 2. API Endpoint Verification via TestClient
    print("\n[Step 2] Testing FastAPI REST API Endpoints...")
    client = TestClient(app)

    # Health check
    res = client.get("/api/v1/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("  [OK] GET /api/v1/health -> status ok")

    # Activities API
    activity_payload = {
        "farmer_id": "test_farmer_01",
        "activity_type": "FERTILIZER_APPLICATION",
        "crop_type": "Maize",
        "description": "Applied 50kg DAP fertilizer to Main Plot",
        "quantity": 50.0,
        "unit": "kg",
        "field_location": "Main Plot",
        "notes": "Applied before forecasted rain",
    }
    create_act_res = client.post("/api/v1/activities", json=activity_payload)
    assert create_act_res.status_code == 201, f"Create activity failed: {create_act_res.text}"
    act_id = create_act_res.json()["id"]
    print(f"  [OK] POST /api/v1/activities -> Created Activity ID #{act_id}")

    get_act_res = client.get(f"/api/v1/activities/{act_id}")
    assert get_act_res.status_code == 200
    assert get_act_res.json()["crop_type"] == "Maize"
    print("  [OK] GET /api/v1/activities/{id} -> Retried created activity")

    list_act_res = client.get("/api/v1/activities?farmer_id=test_farmer_01")
    assert list_act_res.status_code == 200
    assert list_act_res.json()["total"] >= 1
    print("  [OK] GET /api/v1/activities -> Listed farmer activities")

    update_act_res = client.put(f"/api/v1/activities/{act_id}", json={"notes": "Updated note"})
    assert update_act_res.status_code == 200
    assert update_act_res.json()["notes"] == "Updated note"
    print("  [OK] PUT /api/v1/activities/{id} -> Updated activity")

    del_act_res = client.delete(f"/api/v1/activities/{act_id}")
    assert del_act_res.status_code == 204
    print("  [OK] DELETE /api/v1/activities/{id} -> Deleted activity")

    # Weather API
    from unittest.mock import patch, MagicMock
    from datetime import date, timedelta
    mock_dates = [(date.today() + timedelta(days=i)).isoformat() for i in range(7)]
    with patch("app.services.weather_service.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "latitude": -0.4167,
            "longitude": 36.95,
            "timezone": "Africa/Nairobi",
            "daily": {
                "time": mock_dates,
                "temperature_2m_max": [23.0] * 7,
                "temperature_2m_min": [14.0] * 7,
                "precipitation_sum": [0.0] * 7,
                "weathercode": [0] * 7,
            },
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        sync_weather_res = client.post("/api/v1/weather/sync", json={"location_name": "Nyeri"})
        assert sync_weather_res.status_code == 200
        assert sync_weather_res.json()["updated_records"] == 7
        print("  [OK] POST /api/v1/weather/sync -> Synced 7-day forecast for Nyeri")

        get_weather_res = client.get("/api/v1/weather?location_name=Nyeri")
        assert get_weather_res.status_code == 200
        assert len(get_weather_res.json()["cached_forecasts"]) >= 1
        print("  [OK] GET /api/v1/weather -> Retrieved cached weather")

    # Pest & Disease API
    pest_payload = {
        "farmer_id": "test_farmer_01",
        "crop_type": "Maize",
        "issue_type": "PEST",
        "issue_name": "Fall Armyworm",
        "severity": "HIGH",
        "symptoms_description": "Holes in leaves with saw-dust frass",
        "status": "ACTIVE",
    }
    create_pest_res = client.post("/api/v1/pest-disease", json=pest_payload)
    assert create_pest_res.status_code == 201
    pest_id = create_pest_res.json()["id"]
    print(f"  [OK] POST /api/v1/pest-disease -> Created Pest/Disease Record #{pest_id}")

    patch_pest_res = client.patch(f"/api/v1/pest-disease/{pest_id}", json={"status": "RESOLVED"})
    assert patch_pest_res.status_code == 200
    assert patch_pest_res.json()["status"] == "RESOLVED"
    print("  [OK] PATCH /api/v1/pest-disease/{id} -> Updated status to RESOLVED")

    # Extension Directory API
    ext_payload = {
        "name": "Dr. Jane Wanjiru",
        "role_or_type": "EXTENSION_OFFICER",
        "organization": "Ministry of Agriculture",
        "county_region": "Nyeri",
        "phone_number": "+254712345678",
    }
    create_ext_res = client.post("/api/v1/extension-services", json=ext_payload)
    assert create_ext_res.status_code == 201
    print("  [OK] POST /api/v1/extension-services -> Registered Extension Contact")

    search_ext_res = client.get("/api/v1/extension-services?county=Nyeri")
    assert search_ext_res.status_code == 200
    assert search_ext_res.json()["total"] >= 1
    print("  [OK] GET /api/v1/extension-services -> Searched extension directory")

    # 3. Legacy routes check
    print("\n[Step 3] Verifying Legacy Route Aliases...")
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/activities").status_code == 200
    assert client.get("/api/weather?location_name=Nyeri").status_code == 200
    assert client.get("/api/pest-disease").status_code == 200
    assert client.get("/api/extension-services").status_code == 200
    print("  [OK] All legacy alias routes verified successfully.")

    # 4. Static Files & Chat API Verification
    print("\n[Step 4] Verifying Static Files Rendering & Chat API...")
    root_res = client.get("/")
    assert root_res.status_code == 200
    assert "Mkulima Gemma" in root_res.text
    print("  [OK] GET / -> Serves static/index.html")

    css_res = client.get("/static/styles.css")
    assert css_res.status_code == 200
    print("  [OK] GET /static/styles.css -> Serves CSS stylesheet")

    js_res = client.get("/static/app.js")
    assert js_res.status_code == 200
    print("  [OK] GET /static/app.js -> Serves JavaScript logic")

    chat_res = client.post("/api/chat", json={"message": "Fall armyworm control", "language": "English"})
    assert chat_res.status_code == 200
    assert "response" in chat_res.json()
    print("  [OK] POST /api/chat -> Generates AI agronomist chat response")

    print("\n==================================================")
    print("   ALL BACKEND & FRONTEND VERIFICATIONS PASSED!   ")
    print("==================================================")


if __name__ == "__main__":
    run_verification()

