"""
Ground Control Station — FastAPI application entry point.
"""

import json
import logging
import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware

from auth import create_access_token, get_current_user, hash_password, require_commander, verify_password
from database import MissionLog, User, get_db
from robot_client import robot, RobotConnectionError
from models import RegisterRequest, LoginRequest


# ── Configuration ───────────────────────────────────────────────────────────
ROBOT_API_URL = os.getenv("ROBOT_API_URL", "http://localhost:5000")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")


# ── Logging setup ──────────────────────────────────────────────────────────
logging.basicConfig(level=LOG_LEVEL.upper())
logger = logging.getLogger(__name__)


def seed_admin(db):
    existing = db.query(User).filter(User.username == "admin").first()
    if not existing:
        db.add(User(
            username="admin",
            hashed_password=hash_password("admin123"),
            role="commander"
        ))
        db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = next(get_db())
    try:
        seed_admin(db)
        yield
    finally:
        db.close()



# ── Application factory ────────────────────────────────────────────────────
app = FastAPI(
    title="Ground Control Station",
    description="CMP9134 — Robot Management System scaffold",
    version="0.1.0",
    lifespan=lifespan,
)


# ── CORS middleware ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ───────────────────────────────────────────────────────────
@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}


# ── Robot status proxy ─────────────────────────────────────────────────────
@app.get("/api/status")
async def get_status():
    try:
        return await robot.get_status()
    except RobotConnectionError as exc:
        logger.warning("Could not reach robot API: %s", exc)
        return {"error": str(exc)}


# ── Move robot ─────────────────────────────────────────────────────────────
@app.post("/api/move")
async def move(
    x: int,
    y: int,
    current_user: User = Depends(require_commander),
    db=Depends(get_db),
):
    logger.info("Move command from user %s: (%s, %s)", current_user.username, x, y)

    outcome = "success"
    result = None
    try:
        result = await robot.move(x, y)
    except RobotConnectionError as exc:
        logger.warning("Move command failed: %s", exc)
        outcome = str(exc)

    db.add(MissionLog(
        username=current_user.username,
        command="move",
        parameters=json.dumps({"x": x, "y": y}),
        outcome=outcome,
    ))
    db.commit()

    if result is None:
        raise HTTPException(status_code=503, detail=outcome)
    return result
    
@app.get("/api/logs")
async def get_logs(db=Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = db.query(MissionLog).order_by(MissionLog.timestamp.desc()).limit(50).all()
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp,
            "username": log.username,
            "command": log.command,
            "parameters": log.parameters,
            "outcome": log.outcome,
        }
        for log in logs
    ]

# ── WebSocket telemetry ────────────────────────────────────────────────────
@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await robot.get_status()
            await websocket.send_json(data)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        logger.info("Telemetry client disconnected")


# ── User authentication ─────────────────────────────────────────────
@app.post("/auth/register")
async def register(request: RegisterRequest, db=Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = hash_password(request.password)

    new_user = User(
        username=request.username,
        hashed_password=hashed_password,
        role="viewer"   
    )

    db.add(new_user)
    db.commit()

    return {"message": "User registered successfully"}

@app.post("/auth/login")
async def login(request: LoginRequest, db = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    logger.info("User logged in: %s", request.username)
    return {"access_token": access_token, "token_type": "bearer"}

