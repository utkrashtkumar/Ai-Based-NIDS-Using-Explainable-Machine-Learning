"""
Real-Time WebSocket Streaming Channel for AI-NIDS
Streams live classified flows, threat incident alerts, and bandwidth telemetry to the dashboard.
Features a 500ms batch throttle for benign flows and an instant bypass for critical intrusion alerts.
"""

import asyncio
import time
import json
import logging
from typing import List, Dict, Any, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.config import WS_BATCH_INTERVAL_MS

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket Telemetry"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.flow_buffer: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._batch_task: asyncio.Task = None
        self.bytes_last_sec: int = 0
        self.pkts_last_sec: int = 0
        self.total_flows_today: int = 0
        self.threats_today: int = 0

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast_json(self, payload: Dict[str, Any]):
        """Direct broadcast of a single message to all active clients."""
        if not self.active_connections:
            return

        dead_connections = []
        message = json.dumps(payload)
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.active_connections.discard(dead)

    async def enqueue_flow(self, flow: Dict[str, Any]):
        """
        Enqueues a flow into the batch buffer.
        If the flow is a critical threat, it immediately broadcasts to eliminate latency.
        """
        self.total_flows_today += 1
        is_critical = flow.get("is_threat", False) and (flow.get("confidence", 0) >= 0.85)

        if is_critical:
            self.threats_today += 1
            # Immediate broadcast for high-severity alerts
            await self.broadcast_json({
                "type": "CRITICAL_ALERT",
                "flow": flow,
                "timestamp": time.time()
            })

        async with self._lock:
            self.flow_buffer.append(flow)

    async def start_batch_loop(self):
        """Background loop that flushes normal flows every 500ms and sends 1s telemetry."""
        last_telemetry_time = time.time()

        while True:
            await asyncio.sleep(WS_BATCH_INTERVAL_MS / 1000.0)

            # 1. Flush Batched Flows
            flows_to_send = []
            async with self._lock:
                if self.flow_buffer:
                    flows_to_send = self.flow_buffer[:]
                    self.flow_buffer.clear()

            if flows_to_send and self.active_connections:
                await self.broadcast_json({
                    "type": "FLOW_BATCH",
                    "count": len(flows_to_send),
                    "flows": flows_to_send,
                    "timestamp": time.time()
                })

            # 2. Telemetry update every 1 second
            now = time.time()
            if now - last_telemetry_time >= 1.0:
                last_telemetry_time = now
                await self.broadcast_json({
                    "type": "TELEMETRY",
                    "kb_s": round(self.bytes_last_sec / 1024.0, 2),
                    "pkts_s": self.pkts_last_sec,
                    "total_flows": self.total_flows_today,
                    "total_threats": self.threats_today,
                    "clients": len(self.active_connections),
                    "timestamp": now
                })
                self.bytes_last_sec = 0
                self.pkts_last_sec = 0

manager = ConnectionManager()

@router.websocket("/ws/live-traffic")
async def websocket_live_traffic_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep-alive ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket session closed: {e}")
        manager.disconnect(websocket)
