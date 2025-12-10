"""
Pytest configuration and fixtures for HandyMan tests
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.config import settings

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db() -> Generator:
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db) -> Generator:
    """Get a database session"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """Get a test client with overridden database dependency"""
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db_session) -> AsyncGenerator:
    """Get an async test client"""
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_user_data():
    """Mock user data for testing"""
    return {
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test User",
        "phone": "+1234567890"
    }


@pytest.fixture
def mock_job_data():
    """Mock job data for testing"""
    return {
        "title": "Lawn Mowing",
        "description": "Need lawn mowed for medium-sized yard",
        "category": "landscaping",
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "address": "123 Main St, New York, NY"
        },
        "budget_min": 50.0,
        "budget_max": 100.0,
        "preferred_date": "2024-03-15T10:00:00"
    }


@pytest.fixture
def mock_provider_data():
    """Mock provider data for testing"""
    return {
        "email": "provider@example.com",
        "password": "ProviderPass123!",
        "full_name": "John Provider",
        "phone": "+1987654321",
        "services": ["landscaping", "handyman"],
        "hourly_rate": 50.0,
        "radius": 10.0
    }
