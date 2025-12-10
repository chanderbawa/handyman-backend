"""
Tests for authentication endpoints
"""
import pytest
from fastapi.testclient import TestClient


def test_register_user_success(client: TestClient, mock_user_data):
    """Test successful user registration"""
    response = client.post("/api/v1/auth/register", json=mock_user_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == mock_user_data["email"]
    assert "password" not in data  # Password should not be returned


def test_register_duplicate_email(client: TestClient, mock_user_data):
    """Test that registering with duplicate email fails"""
    # Register first user
    client.post("/api/v1/auth/register", json=mock_user_data)
    
    # Try to register again with same email
    response = client.post("/api/v1/auth/register", json=mock_user_data)
    assert response.status_code in [400, 409]


def test_register_invalid_email(client: TestClient, mock_user_data):
    """Test registration with invalid email format"""
    invalid_data = mock_user_data.copy()
    invalid_data["email"] = "invalid-email"
    
    response = client.post("/api/v1/auth/register", json=invalid_data)
    assert response.status_code == 422


def test_register_weak_password(client: TestClient, mock_user_data):
    """Test registration with weak password"""
    weak_data = mock_user_data.copy()
    weak_data["password"] = "123"
    
    response = client.post("/api/v1/auth/register", json=weak_data)
    assert response.status_code in [400, 422]


def test_login_success(client: TestClient, mock_user_data):
    """Test successful login"""
    # Register user first
    client.post("/api/v1/auth/register", json=mock_user_data)
    
    # Login
    login_data = {
        "username": mock_user_data["email"],
        "password": mock_user_data["password"]
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, mock_user_data):
    """Test login with wrong password"""
    # Register user first
    client.post("/api/v1/auth/register", json=mock_user_data)
    
    # Try to login with wrong password
    login_data = {
        "username": mock_user_data["email"],
        "password": "WrongPassword123!"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code in [401, 403]


def test_login_nonexistent_user(client: TestClient):
    """Test login with non-existent user"""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "SomePassword123!"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code in [401, 404]


def test_get_current_user(client: TestClient, mock_user_data):
    """Test getting current user information"""
    # Register and login
    client.post("/api/v1/auth/register", json=mock_user_data)
    
    login_data = {
        "username": mock_user_data["email"],
        "password": mock_user_data["password"]
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Get current user
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == mock_user_data["email"]


def test_unauthorized_access(client: TestClient):
    """Test accessing protected endpoint without token"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_invalid_token(client: TestClient):
    """Test accessing protected endpoint with invalid token"""
    headers = {"Authorization": "Bearer invalid_token_12345"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
