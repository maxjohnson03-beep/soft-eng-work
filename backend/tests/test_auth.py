# test_api.py — integration tests for the Ground Control Station API
#
# These tests use FastAPI's TestClient (which wraps httpx) to make real
# HTTP requests against the app without needing a running server.
#
# The database dependency is overridden to use a separate SQLite test
# database so tests never touch the real gcs.db file.
#
# The robot client is mocked using unittest.mock so tests never need
# a real robot API running.

import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db, MissionLog
from main import app

# ── Test database setup ────────────────────────────────────────────────────
# Use a file-based test DB (not in-memory) so the lifespan seed_admin runs cleanly
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=engine)

client = TestClient(app)


# ── Helpers ────────────────────────────────────────────────────────────────

def get_commander_token() -> str:
    """Return a JWT for the seeded admin/commander account."""
    response = client.post("/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    assert response.status_code == 200, "Admin login failed — is seed_admin running?"
    return response.json()["access_token"]


def get_viewer_token() -> str:
    """Register a viewer account and return its JWT."""
    client.post("/auth/register", json={
        "username": "vieweruser",
        "password": "viewerpass123",
    })
    response = client.post("/auth/login", json={
        "username": "vieweruser",
        "password": "viewerpass123",
    })
    assert response.status_code == 200
    return response.json()["access_token"]


# ── Auth: register ─────────────────────────────────────────────────────────

def test_register_new_user():
    """Registering a new user should return success."""
    response = client.post("/auth/register", json={
        "username": "newuser",
        "password": "securepass123",
    })
    assert response.status_code == 200
    assert response.json()["message"] == "User registered successfully"


def test_register_duplicate_user():
    """Registering the same username twice should return 400."""
    client.post("/auth/register", json={
        "username": "duplicateuser",
        "password": "securepass123",
    })
    response = client.post("/auth/register", json={
        "username": "duplicateuser",
        "password": "securepass123",
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_register_password_too_short():
    """Passwords under 8 characters should be rejected with 422."""
    response = client.post("/auth/register", json={
        "username": "shortpassuser",
        "password": "short",
    })
    assert response.status_code == 422


# ── Auth: login ────────────────────────────────────────────────────────────

def test_login_valid_credentials():
    """Login with correct credentials should return a JWT."""
    client.post("/auth/register", json={
        "username": "loginuser",
        "password": "securepass123",
    })
    response = client.post("/auth/login", json={
        "username": "loginuser",
        "password": "securepass123",
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_wrong_password():
    """Login with wrong password should return 401."""
    response = client.post("/auth/login", json={
        "username": "loginuser",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


def test_login_unknown_user():
    """Login with a username that doesn't exist should return 401."""
    response = client.post("/auth/login", json={
        "username": "ghostuser",
        "password": "doesnotmatter",
    })
    assert response.status_code == 401


# ── Move: RBAC ─────────────────────────────────────────────────────────────
# These tests check that the role-based access control on /api/move works.
# The robot.move call is mocked so no real robot is needed.

def test_move_unauthenticated():
    """Calling /api/move with no token should return 401."""
    response = client.post("/api/move", params={"x": 1, "y": 2})
    assert response.status_code == 401


def test_move_viewer_forbidden():
    """A viewer token should be rejected with 403."""
    token = get_viewer_token()
    response = client.post(
        "/api/move",
        params={"x": 1, "y": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_move_commander_success():
    """A commander token should be allowed and the robot called."""
    token = get_commander_token()
    mock_result = {"status": "moved", "position": {"x": 1, "y": 2}}

    with patch("main.robot.move", new_callable=AsyncMock) as mock_move:
        mock_move.return_value = mock_result
        response = client.post(
            "/api/move",
            params={"x": 1, "y": 2},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == mock_result


# ── Move: mission logging ──────────────────────────────────────────────────

def test_move_logs_success_to_database():
    """A successful move command should write a 'success' entry to mission_logs."""
    token = get_commander_token()
    db = TestingSessionLocal()

    with patch("main.robot.move", new_callable=AsyncMock) as mock_move:
        mock_move.return_value = {"status": "moved"}
        client.post(
            "/api/move",
            params={"x": 3, "y": 4},
            headers={"Authorization": f"Bearer {token}"},
        )

    log = db.query(MissionLog).filter(
        MissionLog.command == "move",
        MissionLog.outcome == "success",
    ).order_by(MissionLog.id.desc()).first()
    db.close()

    assert log is not None
    assert log.username == "admin"
    assert json.loads(log.parameters) == {"x": 3, "y": 4}


def test_move_logs_failure_to_database():
    """A failed move (robot dropout) should still write a log entry with the error."""
    from robot_client import RobotConnectionError
    token = get_commander_token()
    db = TestingSessionLocal()

    with patch("main.robot.move", new_callable=AsyncMock) as mock_move:
        mock_move.side_effect = RobotConnectionError("503 Service Unavailable")
        client.post(
            "/api/move",
            params={"x": 5, "y": 6},
            headers={"Authorization": f"Bearer {token}"},
        )

    log = db.query(MissionLog).filter(
        MissionLog.command == "move",
        MissionLog.outcome != "success",
    ).order_by(MissionLog.id.desc()).first()
    db.close()

    assert log is not None
    assert "503" in log.outcome


def test_move_robot_dropout_returns_503():
    """When the robot is unreachable, /api/move should return 503 to the client."""
    from robot_client import RobotConnectionError
    token = get_commander_token()

    with patch("main.robot.move", new_callable=AsyncMock) as mock_move:
        mock_move.side_effect = RobotConnectionError("Robot unreachable")
        response = client.post(
            "/api/move",
            params={"x": 1, "y": 1},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 503


# ── Logs endpoint ──────────────────────────────────────────────────────────

def test_get_logs_requires_auth():
    """Calling /api/logs without a token should return 401."""
    response = client.get("/api/logs")
    assert response.status_code == 401


def test_get_logs_returns_list():
    """An authenticated user should receive a list of log entries."""
    token = get_commander_token()
    response = client.get(
        "/api/logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── Health ─────────────────────────────────────────────────────────────────

def test_health_check():
    """Health endpoint should always return 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"