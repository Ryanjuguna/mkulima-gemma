import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db
from sqlalchemy import create_engine


@pytest.fixture(autouse=True)
def setup_test_db():
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    init_db(target_engine=test_engine)


def test_root_serves_index_html():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Mkulima Gemma" in response.text
    assert "static/styles.css" in response.text
    assert "static/app.js" in response.text


def test_static_index_html():
    client = TestClient(app)
    response = client.get("/static/index.html")
    assert response.status_code == 200
    assert "Mkulima Gemma" in response.text


def test_static_styles_css():
    client = TestClient(app)
    response = client.get("/static/styles.css")
    assert response.status_code == 200
    assert "background-color" in response.text or "font-family" in response.text


def test_static_app_js():
    client = TestClient(app)
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "addEventListener" in response.text or "loadActivities" in response.text


def test_chat_api_v1():
    client = TestClient(app)
    payload = {
        "message": "How do I control Fall Armyworm in Maize?",
        "language": "English",
        "farmer_id": "test_farmer"
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["language"] == "English"
    assert data["status"] == "success"


def test_chat_api_legacy():
    client = TestClient(app)
    payload = {
        "message": "Nifanye nini Mahindi yakionyesha majani ya manjano?",
        "language": "Swahili",
        "farmer_id": "test_farmer"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Mkulima" in data["response"] or "Mahindi" in data["response"]
    assert data["language"] == "Swahili"
