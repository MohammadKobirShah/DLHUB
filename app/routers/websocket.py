"""
DLHUB - WebSocket Router
==========================
Real-time progress and event streaming.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import logging
import asyncio
import json
from typing import Dict, Set
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from app.queue.client import queue_client

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """WebSocket connection manager."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "progress": set(),
            "events": set(),
            "jobs": set(),
        }

    async def connect(self, websocket: WebSocket, channel: str = "progress"):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        logger.info(f"WebSocket connected to {channel}")

    def disconnect(self, websocket: WebSocket, channel: str = "progress"):
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
        logger.info(f"WebSocket disconnected from {channel}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def broadcast(self, message: dict, channel: str = "progress"):
        if channel not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn, channel)

    async def broadcast_progress(self, job_id: str, progress: dict):
        message = {
            "event": "progress",
            "job_id": job_id,
            "data": progress,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message, "progress")

    async def broadcast_event(self, event_type: str, data: dict):
        message = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message, "events")


manager = ConnectionManager()


@router.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket endpoint for download progress updates."""
    await manager.connect(websocket, "progress")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("action") == "subscribe":
                    job_id = message.get("job_id")
                    logger.info(f"Client subscribed to job {job_id}")
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, "progress")


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket endpoint for system events."""
    await manager.connect(websocket, "events")

    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "events")


@router.websocket("/ws/jobs")
async def websocket_jobs(websocket: WebSocket):
    """WebSocket endpoint for job status updates."""
    await manager.connect(websocket, "jobs")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)

                if message.get("action") == "get_status":
                    job_id = message.get("job_id")
                    if job_id:
                        job = await queue_client.get_job(job_id)
                        progress = await queue_client.get_progress(job_id)

                        await manager.send_personal_message({
                            "event": "job_status",
                            "job_id": job_id,
                            "job": job,
                            "progress": progress
                        }, websocket)

            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, "jobs")


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status."""
    return {
        "active_connections": {
            channel: len(connections)
            for channel, connections in manager.active_connections.items()
        }
    }


async def notify_job_progress(job_id: str, progress: dict):
    """Notify all subscribers of job progress."""
    await manager.broadcast_progress(job_id, progress)


async def notify_job_complete(job_id: str, result: dict):
    """Notify all subscribers of job completion."""
    await manager.broadcast_event("job_complete", {
        "job_id": job_id,
        "result": result
    })


async def notify_job_failed(job_id: str, error: str):
    """Notify all subscribers of job failure."""
    await manager.broadcast_event("job_failed", {
        "job_id": job_id,
        "error": error
    })


async def notify_queue_update(data: dict):
    """Notify all subscribers of queue updates."""
    await manager.broadcast_event("queue_update", data)