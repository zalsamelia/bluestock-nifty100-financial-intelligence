"""
Integration tests for FastAPI /api/v1/companies endpoints.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_get_companies_list():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 90

def test_get_company_profile():
    response = client.get("/api/v1/companies/RELIANCE")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "RELIANCE"

def test_get_company_not_found():
    response = client.get("/api/v1/companies/NONEXISTENT_TICKER_XYZ")
    assert response.status_code == 404

def test_get_company_pl():
    response = client.get("/api/v1/companies/TCS/pl")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_get_company_bs():
    response = client.get("/api/v1/companies/TCS/bs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_company_cashflow():
    response = client.get("/api/v1/companies/TCS/cashflow")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_company_ratios():
    response = client.get("/api/v1/companies/TCS/ratios")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_peers_compare():
    response = client.get("/api/v1/companies/TCS/peers/compare")
    assert response.status_code == 200
    data = response.json()
    assert "target_company" in data
    assert data["target_company"] == "TCS"

def test_get_company_documents():
    response = client.get("/api/v1/companies/TCS/documents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_company_tearsheet_pdf():
    response = client.get("/api/v1/companies/TCS/tearsheet")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 1000
