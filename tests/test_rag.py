"""
Unit tests for Offline AI & RAG Worker (Milestone 3).
Tests SQLite context extraction, RAG prompt formatting, Gemma engine offline fallback,
and REST API endpoints (/api/v1/rag/chat, /api/chat, /api/v1/rag/context-preview).
"""

from datetime import datetime, date, timezone
from unittest.mock import patch
import pytest
from app.models.activity import FarmerActivityLog
from app.models.weather import WeatherCache
from app.models.pest_disease import PestDiseaseHistory
from app.services.rag_service import get_rag_context, build_rag_prompt
from app.services.gemma_engine import query_gemma, OFFLINE_AGRONOMIST_MESSAGE


def test_get_rag_context(db_session):
    """
    Tests extraction of top 5 farmer activities, 3-day weather forecast,
    and active pest/disease records from SQLite database.
    """
    now = datetime.now(timezone.utc)

    # Seed 6 activity logs for farmer_01
    for i in range(1, 7):
        act = FarmerActivityLog(
            farmer_id="farmer_01",
            activity_type="WEEDING",
            crop_type="Maize",
            description=f"Activity number {i}",
            quantity=float(i),
            unit="kg",
            field_location="Plot A",
            logged_at=now,
        )
        db_session.add(act)

    # Seed 4 weather cache entries
    locations = ["Nyeri", "Nyeri", "Nyeri", "Nyeri"]
    dates = [date(2026, 8, 1), date(2026, 8, 2), date(2026, 8, 3), date(2026, 8, 4)]
    for loc, d in zip(locations, dates):
        w = WeatherCache(
            location_name=loc,
            forecast_date=d,
            temp_min_c=14.0,
            temp_max_c=24.0,
            condition_text="Sunny with rain",
            precipitation_mm=5.0,
            humidity_pct=75,
        )
        db_session.add(w)

    # Seed active and resolved pest records
    p1 = PestDiseaseHistory(
        farmer_id="farmer_01",
        crop_type="Maize",
        issue_type="PEST",
        issue_name="Fall Armyworm",
        severity="HIGH",
        symptoms_description="Leaves shredded with frass",
        status="ACTIVE",
        detected_at=now,
    )
    p2 = PestDiseaseHistory(
        farmer_id="farmer_01",
        crop_type="Maize",
        issue_type="DISEASE",
        issue_name="Maize Lethal Necrosis",
        severity="MEDIUM",
        symptoms_description="Yellowing leaves",
        status="RESOLVED",
        detected_at=now,
    )
    db_session.add(p1)
    db_session.add(p2)
    db_session.commit()

    # Extract context
    context = get_rag_context(
        db=db_session,
        farmer_id="farmer_01",
        crop_filter="Maize",
        location="Nyeri",
    )

    assert context["farmer_id"] == "farmer_01"
    assert len(context["farmer_activity_logs"]) == 5  # capped at top 5
    assert len(context["weather_cache"]) == 3  # 3-day forecast
    assert len(context["pest_disease_history"]) == 1  # active only
    assert context["pest_disease_history"][0]["issue_name"] == "Fall Armyworm"


def test_build_rag_prompt_dialects_and_guardrails(db_session):
    """
    Tests RAG prompt formatting across regional dialects (sw, en, kik, luo)
    and verifies chemical safety guardrails are included.
    """
    context = {
        "farmer_id": "test_farmer",
        "crop_filter": "Beans",
        "farmer_activity_logs": [
            {
                "logged_at": "2026-07-31T10:00:00",
                "crop_type": "Beans",
                "activity_type": "PLANTING",
                "description": "Planted Rosecoco seeds",
                "quantity": 10.0,
                "unit": "kg",
                "field_location": "Shamba 1",
            }
        ],
        "weather_cache": [
            {
                "location_name": "Eldoret",
                "forecast_date": "2026-08-01",
                "temp_min_c": 12.0,
                "temp_max_c": 22.0,
                "condition_text": "Light Rain",
                "precipitation_mm": 8.0,
                "humidity_pct": 82,
            }
        ],
        "pest_disease_history": [],
    }

    user_query = "Nitumie dawa gani dhidi ya viwavi?"

    # Swahili test
    sys_sw, prompt_sw = build_rag_prompt(user_query, context, language_dialect="sw")
    assert "Kiswahili" in sys_sw
    assert "CHEMICAL SAFETY" in sys_sw
    assert "Planted Rosecoco seeds" in prompt_sw
    assert "Eldoret" in prompt_sw
    assert user_query in prompt_sw

    # English test
    sys_en, _ = build_rag_prompt(user_query, context, language_dialect="en")
    assert "English" in sys_en

    # Kikuyu test
    sys_kik, _ = build_rag_prompt(user_query, context, language_dialect="kik")
    assert "Gĩkũyũ" in sys_kik

    # Luo test
    sys_luo, _ = build_rag_prompt(user_query, context, language_dialect="luo")
    assert "Dholuo" in sys_luo


def test_gemma_engine_offline_fallback():
    """
    Tests Ollama client handling offline / connection failure scenarios gracefully.
    """
    with patch("httpx.Client.post", side_effect=Exception("Connection refused")):
        res = query_gemma(prompt="Hello Ollama", model="gemma2")
        assert res["is_offline"] is True
        assert res["status"] == "offline"
        assert OFFLINE_AGRONOMIST_MESSAGE in res["response"]


def test_rag_chat_endpoints(client, db_session):
    """
    Tests /api/v1/rag/chat and legacy /api/chat endpoints with mocked Ollama LLM call.
    """
    # Mock Ollama generation response
    mock_llm_response = {
        "response": "Kwa viwavi kwenye mahindi, tumia dawa ya biopesticide au Spinetoram mapema asubuhi.",
        "model": "gemma2",
        "status": "success",
        "is_offline": False,
    }

    with patch("app.api.endpoints.rag.query_gemma", return_value=mock_llm_response):
        # 1. POST /api/v1/rag/chat
        payload_v1 = {
            "prompt": "Viwavi wanakula mahindi yangu, nifanye nini?",
            "farmer_id": "farmer_001",
            "crop_filter": "Maize",
            "language_dialect": "sw",
        }
        res_v1 = client.post("/api/v1/rag/chat", json=payload_v1)
        assert res_v1.status_code == 200
        data_v1 = res_v1.json()
        assert "response" in data_v1
        assert "context_used" in data_v1
        assert data_v1["response"] == mock_llm_response["response"]

        # 2. Legacy POST /api/chat
        payload_legacy = {
            "prompt": "How to treat maize stalk borer?",
            "farmer_id": "farmer_001",
            "language_dialect": "en",
        }
        res_legacy = client.post("/api/chat", json=payload_legacy)
        assert res_legacy.status_code == 200
        data_legacy = res_legacy.json()
        assert "response" in data_legacy


def test_context_preview_endpoint(client, db_session):
    """
    Tests GET /api/v1/rag/context-preview debug endpoint.
    Verifies that system prompt and context breakdown are returned without LLM call.
    """
    res = client.get("/api/v1/rag/context-preview?prompt=Jinsi%20ya%20kupanda&farmer_id=farmer_001&language_dialect=sw")
    assert res.status_code == 200
    data = res.json()
    assert "system_prompt" in data
    assert "formatted_rag_prompt" in data
    assert "context_used" in data
    assert "CHEMICAL SAFETY" in data["system_prompt"]
    assert data["prompt"] == "Jinsi ya kupanda"
