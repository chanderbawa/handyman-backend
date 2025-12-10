"""
Tests for job-related endpoints
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


def test_create_job_success(client: TestClient, mock_user_data, mock_job_data):
    """Test successful job creation"""
    token = get_auth_token(client, mock_user_data)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post("/api/v1/jobs", json=mock_job_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == mock_job_data["title"]
    assert data["status"] == "open"


def test_create_job_unauthorized(client: TestClient, mock_job_data):
    """Test job creation without authentication"""
    response = client.post("/api/v1/jobs", json=mock_job_data)
    assert response.status_code == 401


def test_create_job_invalid_data(client: TestClient, mock_user_data):
    """Test job creation with invalid data"""
    token = get_auth_token(client, mock_user_data)
    headers = {"Authorization": f"Bearer {token}"}
    
    invalid_job = {"title": ""}  # Missing required fields
    response = client.post("/api/v1/jobs", json=invalid_job, headers=headers)
    assert response.status_code == 422


def test_get_jobs_list(client: TestClient, mock_user_data, mock_job_data):
    """Test getting list of jobs"""
    token = get_auth_token(client, mock_user_data)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a job first
    client.post("/api/v1/jobs", json=mock_job_data, headers=headers)
    
    # Get jobs list
    response = client.get("/api/v1/jobs", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_job_by_id(client: TestClient, mock_user_data, mock_job_data):
    """Test getting a specific job by ID"""
    token = get_auth_token(client, mock_user_data)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a job
    create_response = client.post("/api/v1/jobs", json=mock_job_data, headers=headers)
    job_id = create_response.json()["id"]
    
    # Get job by ID
    response = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["title"] == mock_job_data["title"]


def test_get_nonexistent_job(client: TestClient, mock_user_data):
    """Test getting a non-existent job"""
    token = get_auth_token(client, mock_user_data)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/v1/jobs/99999", headers=headers)
    assert response.status_code == 404


def test_update_job(client: TestClient, mock_user_data, mock_job_data):
    """Test updating a job"""
    token = get_auth_token(client, mock_user_data)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a job
    create_response = client.post("/api/v1/jobs", json=mock_job_data, headers=headers)
    job_id = create_response.json()["id"]
    
    # Update the job
    update_data = {"title": "Updated Lawn Mowing", "description": "Updated description"}
    response = client.patch(f"/api/v1/jobs/{job_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]


def test_delete_job(client: TestClient, mock_user_data, mock_job_data):
    """Test deleting a job"""
    token = get_auth_token(client, mock_user_data)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a job
    create_response = client.post("/api/v1/jobs", json=mock_job_data, headers=headers)
    job_id = create_response.json()["id"]
    
    # Delete the job
    response = client.delete(f"/api/v1/jobs/{job_id}", headers=headers)
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert get_response.status_code == 404


def test_search_jobs_by_location(client: TestClient, mock_user_data, mock_job_data):
    """Test searching jobs by location"""
    token = get_auth_token(client, mock_user_data)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a job
    client.post("/api/v1/jobs", json=mock_job_data, headers=headers)
    
    # Search by location
    params = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "radius": 10
    }
    response = client.get("/api/v1/jobs/search", params=params, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_filter_jobs_by_category(client: TestClient, mock_user_data, mock_job_data):
    """Test filtering jobs by category"""
    token = get_auth_token(client, mock_user_data)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a job
    client.post("/api/v1/jobs", json=mock_job_data, headers=headers)
    
    # Filter by category
    params = {"category": "landscaping"}
    response = client.get("/api/v1/jobs", params=params, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
