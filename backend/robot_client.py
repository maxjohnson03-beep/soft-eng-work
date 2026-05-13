"""
Robot API client.

"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

ROBOT_API_URL = os.getenv("ROBOT_API_URL", "http://localhost:5000")

logger = logging.getLogger(__name__)


class RobotConnectionError(Exception):
    """Raised when a request to the robot API fails."""


class RobotClient:
    """Async HTTP client for the Virtual Robot API."""

    def __init__(self, base_url: str = ROBOT_API_URL) -> None:
        self._base = base_url.rstrip("/")

    async def get_status(self) -> dict[str, Any]:
        """Fetch current robot status (position, battery, state)."""
        return await self._get("/api/status")

    async def move(self, x: int, y: int) -> dict[str, Any]:
        """Send a move command to the robot."""
        return await self._post("/api/move", json={"x": x, "y": y})

    async def reset(self) -> dict[str, Any]:
        """Reset the robot simulation."""
        return await self._post("/api/reset")

    async def get_map(self) -> dict[str, Any]:
        """Fetch the robot's current map data."""
        return await self._get("/api/map")

    async def get_sensors(self) -> dict[str, Any]:
        """Fetch the robot's current sensor readings."""
        return await self._get("/api/sensor")

    async def _request_with_retry(
        self, method: str, path: str, **kwargs
    ) -> dict[str, Any]:
        url = f"{self._base}{path}"
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient() as client:
                    response = await getattr(client, method)(url, timeout=5.0, **kwargs)
                    response.raise_for_status()
                    return response.json()
            except Exception as exc:
                if attempt == max_attempts - 1:
                    raise RobotConnectionError(
                        f"Failed after {max_attempts} attempts: {exc}"
                    ) from exc
                wait = (attempt + 1) * 2
                logger.warning(
                    "Request failed (attempt %s/%s), retrying in %ss",
                    attempt + 1,
                    max_attempts,
                    wait,
                )
                await asyncio.sleep(wait)

    async def _get(self, path: str, **kwargs) -> dict[str, Any]:
        return await self._request_with_retry("get", path, **kwargs)

    async def _post(self, path: str, **kwargs) -> dict[str, Any]:
        return await self._request_with_retry("post", path, **kwargs)


robot = RobotClient()
