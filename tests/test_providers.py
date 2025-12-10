"""
Tests for provider-related endpoints
"""
import pytest
from fastapi.testclient import TestClient


def get_auth_token(client: TestClient, user_data: dict) -> str:
    """Helper to register user and get auth token"""
    client.post("/api/v1/auth/register", json=user_data)
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    return response.json()["access_token"]


def test_create_provider_profile(client: TestClient, mock_provider_data):
    """Test creating a provider profile"""
    token = get_auth_token(client, mock_provider_data)
    headers = {"Authorization": f"Bearer {token}"}
    
    provider_profile = {
        "services": ["landscaping", "handyman"],
        "hourly_rate": 50.0,
        "radius": 10.0,
        "bio": "Experienced handyman with 10 years"
    }
    
    response = client.post("/api/v1/providers/profile", json=provider_profile, headers=headers)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["services"] == provider_profile["services"]
    assert data["hourly_rate"] == provider_profile["hourly_rate"]


def test_get_provider_profile(client: TestClient, mock_provider_data):
    """Test getting provider profile"""
    token = get_auth_token(client, mock_provider_data)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create profile first
    provider_profile = {
        "services": ["landscaping"],
        "hourly_rate": 50.0,
        "radius": 10.0
    }
    client.post("/api/v1/providers/profile", json=provider_profile, headers=headers)
    
    # Get profile
    response = client.get("/api/v1/providers/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert "hourly_rate" in data


def test_update_provider_profile(client: TestClient, mock_provider_data):
    """Test updating provider profile"""
    token = get_auth_token(client, mock_provider_data)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create profile
    provider_profile = {
        "services": ["landscaping"],
        "hourly_rate": 50.0,
        "radius": 10.0
    }
    client.post("/api/v1/providers/profile", json=provider_profile, headers=headers)
    
    # Update profile
    update_data = {"hourly_rate": 60.0, "radius": 15.0}
    response = client.patch("/api/v1/providers/me", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["hourly_rate"] == 60.0


def test_get_available_jobs_for_provider(client: TestClient, mock_provider_data, mock_user_data, mock_job_data):
    """Test getting available jobs for a provider"""
    # Create a client with a job
    client_token = get_auth_token(client, mock_user_data)
    client_headers = {"Authorization": f"Bearer {client_token}"}
    client.post("/api/v1/jobs", json=mock_job_data, headers=client_headers)
    
    # Create provider
    provider_token = get_auth_token(client, mock_provider_data)
    provider_headers = {"Authorization": f"Bearer {provider_token}"}
    
    provider_profile = {
        "services": ["landscaping"],
        "hourly_rate": 50.0,
        "radius": 50.0,
        "location": {"latitude": 40.7128, "longitude": -74.0060}
    }
    client.post("/api/v1/providers/profile", json=provider_profile, headers=provider_headers)
    
    # Get available jobs
    response = client.get("/api/v1/providers/available-jobs", headers=provider_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_accept_job(client: TestClient, mock_provider_data, mock_user_data, mock_job_data):
    """Test provider accepting a job"""
    # Create job
    client_token = get_auth_token(client, mock_user_data)
    client_headers = {"Authorization": f"Bearer {client_token}"}
    job_response = client.post("/api/v1/jobs", json=mock_job_data, headers=client_headers)
    job_id = job_response.json()["id"]
    
    # Create provider
    provider_token = get_auth_token(client, mock_provider_data)
    provider_headers = {"Authorization": f"Bearer {provider_token}"}
    
    # Accept job
    response = client.post(f"/api/v1/providers/jobs/{job_id}/accept", headers=provider_headers)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["status"] in ["accepted", "in_progress"]


def test_complete_job(client: TestClient, mock_provider_data, mock_user_data, mock_job_data):
    """Test provider completing a job"""
    # Create and accept job
    client_token = get_auth_token(client, mock_user_data)
    client_headers = {"Authorization": f"Bearer {client_token}"}
    job_response = client.post("/api/v1/jobs", json=mock_job_data, headers=client_headers)
    job_id = job_response.json()["id"]
    
    provider_token = get_auth_token(client, mock_provider_data)
    provider_headers = {"Authorization": f"Bearer {provider_token}"}
    client.post(f"/api/v1/providers/jobs/{job_id}/accept", headers=provider_headers)
    
    # Complete job
    completion_data = {"notes": "Job completed successfully"}
    response = client.post(f"/api/v1/providers/jobs/{job_id}/complete", json=completion_data, headers=provider_headers)
    assert response.status_code in [200, 201]


def test_get_provider_statistics(client: TestClient, mock_provider_data):
    """Test getting provider statistics"""
    token = get_auth_token(client, mock_provider_data)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/v1/providers/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_jobs" in data or "completed_jobs" in data


def test_search_providers(client: TestClient, mock_provider_data):
    """Test searching for providers"""
    # Create provider profile
    token = get_auth_token(client, mock_provider_data)
    headers = {"Authorization": f"Bearer {token}"}
    
    provider_profile = {
        "services": ["landscaping"],
        "hourly_rate": 50.0,
        "radius": 10.0
    }
    client.post("/api/v1/providers/profile", json=provider_profile, headers=headers)
    
    # Search providers
    params = {"service": "landscaping"}
    response = client.get("/api/v1/providers/search", params=params, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
