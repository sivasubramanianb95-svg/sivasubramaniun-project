import os
os.environ["IMAGE_PROVIDER"] = "mock"
os.environ["GEMINI_API_KEY"] = ""
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings

client = TestClient(app)

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "ComicCraft" in response.text

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_json_generation_end_to_end():
    payload = {"story_prompt":"A brave fox explores an enchanted forest", "character_name":"Finn", "setting":"forest", "tone":"dramatic", "art_style":"anime"}
    response = client.post("/generate-comic/json", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["success"] is True
    assert len(data["layout"]) == 5
    assert data["pdf_path"].endswith(".pdf")

def test_image_endpoint():
    response = client.post("/test-image", json={"prompt":"a fox in a forest"})
    assert response.status_code == 200
    assert response.json()["image_path"].startswith("/static/panels/")
