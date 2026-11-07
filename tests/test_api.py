from fastapi.testclient import TestClient
from app.main import app, cfg

client=TestClient(app)

def test_health_without_model_or_key():
    result=client.get("/api/health")
    assert result.status_code==200 and result.json()["status"]=="ok"
def test_empty_chat_rejected():
    assert client.post("/api/chat",json={"question":""}).status_code==422
def test_missing_key_is_technical_failure(monkeypatch):
    monkeypatch.setattr(cfg,"gemini_api_key","")
    result=client.post("/api/chat",json={"question":"شو شروط الانسحاب؟"})
    assert result.status_code==503
    assert "GEMINI_API_KEY" in result.json()["detail"]
def test_admin_locked_by_default(monkeypatch):
    monkeypatch.setattr(cfg,"admin_token","")
    assert client.post("/api/documents/ingest").status_code==403
