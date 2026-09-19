"""
Integration tests for FastAPI /api/v1/health endpoint.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_endpoint_status():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "uptime_seconds" in data
    assert "db_row_counts" in data

def test_health_table_row_counts():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    tables = response.json()["db_row_counts"]
    expected_tables = [
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "financial_ratios",
    ]
    for tbl in expected_tables:
        assert tbl in tables
        assert tables[tbl] > 0
