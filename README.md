# Ground Control Station — CMP9134

A web-based Ground Control Station for monitoring and controlling a virtual robot, built for the CMP9134 Software Engineering assessment at the University of Lincoln.

## Features

- **Live dashboard** — real-time robot position, battery level, and connection status
- **Move controls** — send coordinate commands to the robot with visual feedback
- **Role-based access control** — viewer and commander roles enforced via JWT authentication
- **Mission logging** — every command is persisted to a SQLite database with timestamp, user, and outcome
- **Error handling** — retry logic with exponential backoff, Signal Lost indicator on robot dropout
- **WebSocket telemetry** — real-time status stream from the backend
- **Automated tests** — 20 tests across unit and integration layers, running in CI on every push

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/maxjohnson03-beep/soft-eng-work

# 2. Copy the environment file
cp .env.example .env

# 3. Start the full stack
docker compose up --build

# 4. Open the dashboard
open http://localhost:8080
```

Default port: **8080**. Change via `GCS_PORT` in `.env`.

## Default Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | commander |

Additional users can be registered via the dashboard. All registered users are assigned the viewer role.

## Architecture

```
Browser → Nginx (port 8080) → FastAPI (port 8000) → Robot API (port 5000)
                                      ↓
                                 SQLite (gcs.db)
```

Three containers orchestrated via Docker Compose:
- **robot-api** — virtual robot simulator (provided)
- **backend** — FastAPI application handling auth, business logic, and database
- **frontend** — Nginx serving the static dashboard and proxying API requests

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /health | None | Health check |
| POST | /auth/register | None | Register a new viewer account |
| POST | /auth/login | None | Login and receive JWT |
| GET | /api/status | None | Robot status |
| POST | /api/move | Commander | Send move command |
| POST | /api/reset | Commander | Reset robot simulation |
| GET | /api/sensors | None | Sensor readings |
| GET | /api/logs | Authenticated | Mission log entries |
| WS | /ws/telemetry | None | Real-time telemetry stream |

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

## Project Structure

```
├── backend/
│   ├── Dockerfile          # Multi-stage: base / development / production
│   ├── main.py             # FastAPI application — routes and business logic
│   ├── auth.py             # JWT authentication and RBAC
│   ├── database.py         # SQLAlchemy models (User, MissionLog)
│   ├── robot_client.py     # Async robot HTTP client with retry logic
│   ├── models.py           # Pydantic request models
│   ├── requirements.txt    # Python dependencies
│   └── tests/
│       ├── conftest.py     # Test database setup and fixtures
│       ├── test_api.py     # Integration tests
│       └── test_auth.py    # Unit tests
├── frontend/
│   ├── Dockerfile          # Nginx serving static files
│   ├── nginx.conf          # Reverse proxy configuration
│   └── public/
│       └── index.html      # Dashboard — login, controls, map, audit log
├── .devcontainer/          # VS Code Dev Container configuration
├── .github/workflows/      # GitHub Actions CI pipeline
├── docker-compose.yml      # Stack orchestration
└── .env.example            # Environment variable template
```

## CI/CD

GitHub Actions runs on every push to main and every pull request:
1. **test** — runs pytest across Python 3.11 and 3.12
2. **compose-test** — builds the full Docker stack and smoke tests the health endpoint
