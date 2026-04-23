"""
Robot API client scaffold.

Provides a small async wrapper around the Virtual Robot REST API.
Students should extend this with retry logic, error handling, and
any additional endpoints exposed by the robot simulator.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

ROBOT_API_URL = os.getenv("ROBOT_API_URL", "http://localhost:5000")

logger = logging.getLogger(__name__)


class RobotConnectionError(Exception):
    """Raised when a request to the robot API fails."""


class RobotClient:
    """Minimal async HTTP client for the Virtual Robot API."""

    def __init__(self, base_url: str = ROBOT_API_URL) -> None:
        self._base = base_url.rstrip("/")

    async def get_status(self) -> dict[str, Any]:
        """Fetch current robot status (position, battery, state)."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self._base}/api/status", timeout=5.0)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            raise RobotConnectionError(f"Robot unreachable: {exc}") from exc

async def move(self, x: int, y: int) -> dict[str, Any]:
    """Send a move command to the robot."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self._base}/api/move", json={"x": x, "y": y}, timeout=5.0)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        raise RobotConnectionError(f"Move command failed: {exc}") from exc
    

async def reset(self) -> dict[str, Any]:
        """Reset the robot simulation."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self._base}/api/reset", timeout=5.0)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            raise RobotConnectionError(f"Reset command failed: {exc}") from exc   


    # TODO: add get_map(), get_sensors(), etc. as needed
async def get_map(self): 
    """Fetch the robot's current map data."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self._base}/api/map", timeout=5.0)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        raise RobotConnectionError(f"Get map failed: {exc}") from exc
    
async def get_sensors(self):
    """Fetch the robot's current sensor readings."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self._base}/api/sensor", timeout=5.0)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        raise RobotConnectionError(f"Get sensors failed: {exc}") from exc
    

# Module-level singleton used by main.py
robot = RobotClient()



