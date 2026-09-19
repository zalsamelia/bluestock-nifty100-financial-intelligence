"""
Integration tests for FastAPI /api/v1/sectors endpoints.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_get_sectors():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    data = response.json()
    # /api/v1/sectors returns a list of sector objects
    assert isinstance(data, list)
    assert len(data) > 0

def test_get_sector_companies():
    response = client.get("/api/v1/sectors/Information Technology/companies")
    assert response.status_code == 200
    data = response.json()
    # /api/v1/sectors/{sector}/companies returns {"sector": ..., "count": ..., "companies": [...]}
    assert "companies" in data or isinstance(data, list)
    if isinstance(data, dict):
        companies = data.get("companies", data)
    else:
        companies = data
    assert len(companies) > 0

def test_get_sector_not_found():
    response = client.get("/api/v1/sectors/NonExistentSector12345/companies")
    assert response.status_code == 404
