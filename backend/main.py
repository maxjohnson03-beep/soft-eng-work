"""
Ground Control Station — FastAPI application entry point.
"""

import logging
import os
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from robot_client import robot, RobotConnectionError


# ── Configuration ───────────────────────────────────────────────────────────
ROBOT_API_URL = os.getenv("ROBOT_API_URL", "http://localhost:5000")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")


# ── Logging setup ──────────────────────────────────────────────────────────
logging.basicConfig(level=LOG_LEVEL.upper())
logger = logging.getLogger(__name__)


# ── Application factory ────────────────────────────────────────────────────
app = FastAPI(
    title="Ground Control Station",
    description="CMP9134 — Robot Management System scaffold",
    version="0.1.0",
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
async def move(x: int, y: int):
    try:
        return await robot.move(x, y)
    except RobotConnectionError as exc:
        logger.warning("Move command failed: %s", exc)
        return {"error": str(exc)}


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
