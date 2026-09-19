"""
Integration tests for FastAPI /api/v1/screener endpoint.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_screener_default():
    response = client.get("/api/v1/screener")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "data" in data

def test_screener_roe_filter():
    response = client.get("/api/v1/screener?min_roe=15")
    assert response.status_code == 200
    data = response.json()
    for row in data["data"]:
        if row.get("return_on_equity_pct") is not None:
            assert row["return_on_equity_pct"] >= 15.0

def test_screener_sector_filter():
    response = client.get("/api/v1/screener?sector=Information Technology")
    assert response.status_code == 200
    data = response.json()
    for row in data["data"]:
        assert row["sector"] == "Information Technology"

def test_screener_invalid_bounds():
    response = client.get("/api/v1/screener?min_roe=50&max_roe=10")
    assert response.status_code == 400
