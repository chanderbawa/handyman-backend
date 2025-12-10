"""
Tests for main application endpoints
"""
import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test the root endpoint returns correct information"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data
    assert data["message"] == "HandyMan API"


def test_health_check(client: TestClient):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_docs_endpoint_accessible(client: TestClient):
    """Test that API docs are accessible"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_endpoint_accessible(client: TestClient):
    """Test that ReDoc is accessible"""
    response = client.get("/redoc")
    assert response.status_code == 200


def test_cors_headers(client: TestClient):
    """Test that CORS headers are properly configured"""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_invalid_endpoint_returns_404(client: TestClient):
    """Test that invalid endpoints return 404"""
    response = client.get("/invalid/endpoint")
    assert response.status_code == 404
