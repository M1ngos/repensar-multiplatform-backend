# app/core/sse_manager.py
"""
Server-Sent Events (SSE) Manager for real-time notification delivery.
Manages client connections and broadcasts notifications via EventBus.
"""
import asyncio
import json
import logging
from typing import Dict, Set, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class SSEConnection:
    """Represents a single SSE connection for a user."""

    def __init__(self, user_id: int, connection_id: str):
        self.user_id = user_id
        self.connection_id = connection_id
        self.queue: asyncio.Queue = asyncio.Queue()
        self.connected_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()

    async def send_event(self, event_type: str, data: dict):
        """Queue an event to be sent to the client."""
        await self.queue.put({
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def send_heartbeat(self):
        """Send a heartbeat ping to keep the connection alive."""
        self.last_heartbeat = datetime.utcnow()
        await self.queue.put({
            "event": "ping",
            "data": {"timestamp": self.last_heartbeat.isoformat()}
        })


class SSEManager:
    """
    Manages Server-Sent Events connections for real-time notifications.
    Supports multiple connections per user across different devices/tabs.
    """

    def __init__(self):
        # user_id -> set of SSEConnection objects
        self.connections: Dict[int, Set[SSEConnection]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def connect(self, user_id: int, connection_id: str) -> SSEConnection:
        """
        Register a new SSE connection for a user.

        Args:
            user_id: User ID
            connection_id: Unique connection identifier

        Returns:
            SSEConnection object
        """
        connection = SSEConnection(user_id, connection_id)

        async with self._lock:
            self.connections[user_id].add(connection)

        logger.info(f"SSE connection established for user {user_id} (connection {connection_id})")
        logger.debug(f"Total active connections for user {user_id}: {len(self.connections[user_id])}")

        return connection

    async def disconnect(self, user_id: int, connection_id: str):
        """
        Remove an SSE connection.

        Args:
            user_id: User ID
            connection_id: Connection identifier to remove
        """
        async with self._lock:
            if user_id in self.connections:
                # Find and remove the connection
                self.connections[user_id] = {
                    conn for conn in self.connections[user_id]
                    if conn.connection_id != connection_id
                }

                # Clean up empty sets
                if not self.connections[user_id]:
                    del self.connections[user_id]

        logger.info(f"SSE connection closed for user {user_id} (connection {connection_id})")

    async def broadcast_to_user(self, user_id: int, event_type: str, data: dict):
        """
        Broadcast an event to all connections for a specific user.

        Args:
            user_id: User ID to send to
            event_type: Type of event (e.g., "notification", "update")
            data: Event payload
        """
        if user_id not in self.connections:
            logger.debug(f"No active SSE connections for user {user_id}")
            return

        connections = self.connections[user_id].copy()
        logger.debug(f"Broadcasting {event_type} to {len(connections)} connections for user {user_id}")

        for connection in connections:
            try:
                await connection.send_event(event_type, data)
            except Exception as e:
                logger.error(f"Error sending event to connection {connection.connection_id}: {e}")

    async def broadcast_to_all(self, event_type: str, data: dict):
        """
        Broadcast an event to all connected users.

        Args:
            event_type: Type of event
            data: Event payload
        """
        all_connections = []
        for user_connections in self.connections.values():
            all_connections.extend(user_connections)

        logger.debug(f"Broadcasting {event_type} to {len(all_connections)} total connections")

        for connection in all_connections:
            try:
                await connection.send_event(event_type, data)
            except Exception as e:
                logger.error(f"Error broadcasting to connection {connection.connection_id}: {e}")

    def get_connection_count(self, user_id: Optional[int] = None) -> int:
        """
        Get the number of active connections.

        Args:
            user_id: Optional user ID to get count for specific user

        Returns:
            Connection count
        """
        if user_id:
            return len(self.connections.get(user_id, set()))

        return sum(len(conns) for conns in self.connections.values())

    def get_connected_users(self) -> Set[int]:
        """
        Get set of all user IDs with active connections.

        Returns:
            Set of user IDs
        """
        return set(self.connections.keys())

    async def heartbeat_loop(self, interval: int = 30):
        """
        Send periodic heartbeat pings to all connections.

        Args:
            interval: Seconds between heartbeats (default: 30)
        """
        while True:
            try:
                await asyncio.sleep(interval)

                all_connections = []
                for user_connections in self.connections.values():
                    all_connections.extend(user_connections)

                for connection in all_connections:
                    try:
                        await connection.send_heartbeat()
                    except Exception as e:
                        logger.error(f"Error sending heartbeat: {e}")

                logger.debug(f"Heartbeat sent to {len(all_connections)} connections")

            except asyncio.CancelledError:
                logger.info("Heartbeat loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

    async def start_heartbeat(self, interval: int = 30):
        """Start the heartbeat background task."""
        if not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self.heartbeat_loop(interval))
            logger.info(f"SSE heartbeat started (interval: {interval}s)")

    async def stop_heartbeat(self):
        """Stop the heartbeat background task."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            logger.info("SSE heartbeat stopped")

    async def cleanup_stale_connections(self, timeout_seconds: int = 300):
        """
        Remove connections that haven't received a heartbeat acknowledgment.

        Args:
            timeout_seconds: Seconds of inactivity before considering connection stale
        """
        now = datetime.utcnow()
        stale_connections = []

        for user_id, connections in self.connections.items():
            for connection in connections:
                time_since_heartbeat = (now - connection.last_heartbeat).total_seconds()
                if time_since_heartbeat > timeout_seconds:
                    stale_connections.append((user_id, connection.connection_id))

        for user_id, connection_id in stale_connections:
            await self.disconnect(user_id, connection_id)
            logger.info(f"Removed stale SSE connection: user {user_id}, connection {connection_id}")

        return len(stale_connections)


# Global SSE manager instance (will be initialized in main.py)
sse_manager: Optional[SSEManager] = None


def get_sse_manager() -> SSEManager:
    """Get the global SSE manager instance."""
    if sse_manager is None:
        raise RuntimeError("SSEManager not initialized. Call initialize_sse_manager() first.")
    return sse_manager
