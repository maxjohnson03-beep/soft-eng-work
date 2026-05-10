# test_api.py — integration tests for register and login endpoints

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app

# Use a separate in-memory database for testing
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the database dependency to use the test database
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create tables in test database
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_register_new_user():
    """Registering a new user should return success."""
    response = client.post("/auth/register", json={
        "username": "testuser",
        "password": "testpass",
        "role": "viewer"
    })
    assert response.status_code == 200
    assert response.json()["message"] == "User registered successfully"

def test_register_duplicate_user():
    """Registering the same username twice should fail."""
    client.post("/auth/register", json={
        "username": "duplicateuser",
        "password": "testpass",
        "role": "viewer"
    })
    response = client.post("/auth/register", json={
        "username": "duplicateuser",
        "password": "testpass",
        "role": "viewer"
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_login_valid_credentials():
    """Login with correct credentials should return a token."""
    client.post("/auth/register", json={
        "username": "loginuser",
        "password": "testpass",
        "role": "commander"
    })
    response = client.post("/auth/login", json={
        "username": "loginuser",
        "password": "testpass"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_credentials():
    """Login with wrong password should fail."""
    response = client.post("/auth/login", json={
        "username": "loginuser",
        "password": "wrongpassword"
    })
    assert response.status_code == 401