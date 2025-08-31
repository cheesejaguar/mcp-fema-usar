"""Real-time communications module for FEMA USAR MCP.

Provides WebSocket-based real-time communications, push notifications,
and coordination capabilities for USAR operations.
"""

import asyncio
import json
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import aioredis
from aiohttp import WSMsgType, web

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Real-time message types."""

    # System messages
    HEARTBEAT = "heartbeat"
    AUTHENTICATION = "auth"
    SUBSCRIPTION = "subscribe"
    UNSUBSCRIPTION = "unsubscribe"

    # Operational messages
    DEPLOYMENT_UPDATE = "deployment_update"
    PERSONNEL_STATUS = "personnel_status"
    EQUIPMENT_STATUS = "equipment_status"
    SAFETY_ALERT = "safety_alert"
    OPERATION_UPDATE = "operation_update"
    MISSION_ASSIGNMENT = "mission_assignment"

    # Coordination messages
    CHAT_MESSAGE = "chat_message"
    LOCATION_UPDATE = "location_update"
    RESOURCE_REQUEST = "resource_request"
    SITUATION_REPORT = "situation_report"

    # Notifications
    NOTIFICATION = "notification"
    ALERT = "alert"
    BROADCAST = "broadcast"


class Priority(Enum):
    """Message priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class Channel:
    """Communication channel types."""

    # Global channels
    GLOBAL = "global"
    SYSTEM = "system"
    ALERTS = "alerts"

    # Operational channels
    COMMAND = "command"
    OPERATIONS = "operations"
    SAFETY = "safety"
    LOGISTICS = "logistics"

    # Task force channels
    @staticmethod
    def task_force(task_force_id: str) -> str:
        return f"tf_{task_force_id}"

    # Deployment channels
    @staticmethod
    def deployment(deployment_id: str) -> str:
        return f"deployment_{deployment_id}"

    # Functional group channels
    @staticmethod
    def functional_group(group: str, task_force_id: str) -> str:
        return f"fg_{group}_{task_force_id}"

    # Private channels
    @staticmethod
    def private(user_id: str) -> str:
        return f"user_{user_id}"


@dataclass
class Message:
    """Real-time message model."""

    id: str
    type: MessageType
    channel: str
    sender: str
    recipient: str | None
    content: dict[str, Any]
    priority: Priority
    timestamp: datetime
    expires_at: datetime | None = None
    requires_ack: bool = False
    metadata: dict[str, Any] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "channel": self.channel,
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "requires_ack": self.requires_ack,
            "metadata": self.metadata or {},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=MessageType(data["type"]),
            channel=data["channel"],
            sender=data["sender"],
            recipient=data.get("recipient"),
            content=data["content"],
            priority=Priority(data["priority"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if data.get("expires_at")
                else None
            ),
            requires_ack=data.get("requires_ack", False),
            metadata=data.get("metadata", {}),
        )


class WebSocketConnection:
    """WebSocket connection wrapper."""

    def __init__(self, websocket: web.WebSocketResponse, user_id: str, user_role: str):
        """Initialize WebSocket connection.

        Args:
            websocket: WebSocket response object
            user_id: Connected user ID
            user_role: User role
        """
        self.websocket = websocket
        self.user_id = user_id
        self.user_role = user_role
        self.id = str(uuid.uuid4())
        self.connected_at = datetime.now(UTC)
        self.last_heartbeat = datetime.now(UTC)
        self.subscribed_channels: set[str] = set()
        self.message_queue: list[Message] = []
        self.is_authenticated = False

    async def send_message(self, message: Message):
        """Send message to WebSocket.

        Args:
            message: Message to send
        """
        try:
            if not self.websocket.closed:
                await self.websocket.send_str(json.dumps(message.to_dict()))
        except Exception as e:
            logger.error(f"Failed to send message to {self.user_id}: {str(e)}")

    async def close(self, code: int = 1000, message: str = "Connection closed"):
        """Close WebSocket connection.

        Args:
            code: Close code
            message: Close message
        """
        try:
            if not self.websocket.closed:
                await self.websocket.close(code=code, message=message.encode())
        except Exception as e:
            logger.error(f"Error closing WebSocket for {self.user_id}: {str(e)}")

    def is_alive(self) -> bool:
        """Check if connection is alive."""
        return not self.websocket.closed

    def update_heartbeat(self):
        """Update last heartbeat timestamp."""
        self.last_heartbeat = datetime.now(UTC)


class ChannelManager:
    """Channel subscription and management."""

    def __init__(self):
        """Initialize channel manager."""
        self.subscriptions: dict[str, set[str]] = {}  # channel -> connection_ids
        self.connection_channels: dict[str, set[str]] = {}  # connection_id -> channels

    def subscribe(self, connection_id: str, channel: str):
        """Subscribe connection to channel.

        Args:
            connection_id: Connection identifier
            channel: Channel name
        """
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()
        self.subscriptions[channel].add(connection_id)

        if connection_id not in self.connection_channels:
            self.connection_channels[connection_id] = set()
        self.connection_channels[connection_id].add(channel)

        logger.debug(f"Connection {connection_id} subscribed to {channel}")

    def unsubscribe(self, connection_id: str, channel: str):
        """Unsubscribe connection from channel.

        Args:
            connection_id: Connection identifier
            channel: Channel name
        """
        if channel in self.subscriptions:
            self.subscriptions[channel].discard(connection_id)
            if not self.subscriptions[channel]:
                del self.subscriptions[channel]

        if connection_id in self.connection_channels:
            self.connection_channels[connection_id].discard(channel)
            if not self.connection_channels[connection_id]:
                del self.connection_channels[connection_id]

        logger.debug(f"Connection {connection_id} unsubscribed from {channel}")

    def unsubscribe_all(self, connection_id: str):
        """Unsubscribe connection from all channels.

        Args:
            connection_id: Connection identifier
        """
        if connection_id in self.connection_channels:
            channels = self.connection_channels[connection_id].copy()
            for channel in channels:
                self.unsubscribe(connection_id, channel)

    def get_subscribers(self, channel: str) -> set[str]:
        """Get subscribers for channel.

        Args:
            channel: Channel name

        Returns:
            Set of connection IDs
        """
        return self.subscriptions.get(channel, set()).copy()

    def get_channels(self, connection_id: str) -> set[str]:
        """Get channels for connection.

        Args:
            connection_id: Connection identifier

        Returns:
            Set of channel names
        """
        return self.connection_channels.get(connection_id, set()).copy()


class MessageBroker:
    """Message broker for real-time communications."""

    def __init__(self, redis_url: str | None = None):
        """Initialize message broker.

        Args:
            redis_url: Redis connection URL for clustering
        """
        self.redis_url = redis_url
        self.redis_client: aioredis.Redis | None = None
        self.connections: dict[str, WebSocketConnection] = {}
        self.channel_manager = ChannelManager()
        self.message_handlers: dict[MessageType, list[Callable]] = {}
        self.running = False

    async def initialize(self):
        """Initialize message broker."""
        if self.redis_url:
            self.redis_client = aioredis.from_url(self.redis_url)
            logger.info("Connected to Redis for message clustering")

        self.running = True

        # Start background tasks
        asyncio.create_task(self._heartbeat_task())
        asyncio.create_task(self._cleanup_task())

        if self.redis_client:
            asyncio.create_task(self._redis_subscriber_task())

        logger.info("Message broker initialized")

    async def shutdown(self):
        """Shutdown message broker."""
        self.running = False

        # Close all connections
        for connection in list(self.connections.values()):
            await connection.close()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("Message broker shutdown")

    def add_connection(self, connection: WebSocketConnection):
        """Add WebSocket connection.

        Args:
            connection: WebSocket connection
        """
        self.connections[connection.id] = connection

        # Auto-subscribe to user's private channel
        private_channel = Channel.private(connection.user_id)
        self.channel_manager.subscribe(connection.id, private_channel)
        connection.subscribed_channels.add(private_channel)

        logger.info(
            f"Added WebSocket connection: {connection.id} (user: {connection.user_id})"
        )

    def remove_connection(self, connection_id: str):
        """Remove WebSocket connection.

        Args:
            connection_id: Connection identifier
        """
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            self.channel_manager.unsubscribe_all(connection_id)
            del self.connections[connection_id]
            logger.info(
                f"Removed WebSocket connection: {connection_id} (user: {connection.user_id})"
            )

    async def publish_message(self, message: Message):
        """Publish message to channel.

        Args:
            message: Message to publish
        """
        # Store message if persistent
        if self.redis_client and message.requires_ack:
            await self.redis_client.lpush(
                f"messages:{message.channel}", json.dumps(message.to_dict())
            )
            await self.redis_client.expire(
                f"messages:{message.channel}", 3600
            )  # 1 hour

        # Send to local subscribers
        await self._deliver_local_message(message)

        # Publish to Redis for clustering
        if self.redis_client:
            await self.redis_client.publish(
                f"channel:{message.channel}", json.dumps(message.to_dict())
            )

        # Call message handlers
        if message.type in self.message_handlers:
            for handler in self.message_handlers[message.type]:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Message handler error: {str(e)}")

    async def _deliver_local_message(self, message: Message):
        """Deliver message to local connections.

        Args:
            message: Message to deliver
        """
        subscribers = self.channel_manager.get_subscribers(message.channel)

        # Add specific recipient if set
        if message.recipient:
            recipient_connections = [
                conn
                for conn in self.connections.values()
                if conn.user_id == message.recipient
            ]
            for conn in recipient_connections:
                subscribers.add(conn.id)

        # Send to all subscribers
        for connection_id in subscribers:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                if connection.is_alive():
                    await connection.send_message(message)

    async def handle_websocket_message(
        self, connection: WebSocketConnection, data: str
    ):
        """Handle WebSocket message from client.

        Args:
            connection: WebSocket connection
            data: Message data
        """
        try:
            message_data = json.loads(data)
            message_type = MessageType(message_data.get("type"))

            if message_type == MessageType.HEARTBEAT:
                connection.update_heartbeat()
                await connection.send_message(
                    Message(
                        id=str(uuid.uuid4()),
                        type=MessageType.HEARTBEAT,
                        channel=Channel.private(connection.user_id),
                        sender="system",
                        recipient=connection.user_id,
                        content={"status": "alive"},
                        priority=Priority.LOW,
                        timestamp=datetime.now(UTC),
                    )
                )

            elif message_type == MessageType.SUBSCRIPTION:
                channel = message_data.get("channel")
                if channel and self._can_subscribe(connection, channel):
                    self.channel_manager.subscribe(connection.id, channel)
                    connection.subscribed_channels.add(channel)

            elif message_type == MessageType.UNSUBSCRIPTION:
                channel = message_data.get("channel")
                if channel:
                    self.channel_manager.unsubscribe(connection.id, channel)
                    connection.subscribed_channels.discard(channel)

            else:
                # Regular message
                message = Message(
                    id=str(uuid.uuid4()),
                    type=message_type,
                    channel=message_data.get("channel", Channel.GLOBAL),
                    sender=connection.user_id,
                    recipient=message_data.get("recipient"),
                    content=message_data.get("content", {}),
                    priority=Priority(message_data.get("priority", "normal")),
                    timestamp=datetime.now(UTC),
                    requires_ack=message_data.get("requires_ack", False),
                )

                await self.publish_message(message)

        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}")
            await connection.send_message(
                Message(
                    id=str(uuid.uuid4()),
                    type=MessageType.NOTIFICATION,
                    channel=Channel.private(connection.user_id),
                    sender="system",
                    recipient=connection.user_id,
                    content={"error": "Invalid message format"},
                    priority=Priority.NORMAL,
                    timestamp=datetime.now(UTC),
                )
            )

    def _can_subscribe(self, connection: WebSocketConnection, channel: str) -> bool:
        """Check if connection can subscribe to channel.

        Args:
            connection: WebSocket connection
            channel: Channel name

        Returns:
            True if subscription allowed
        """
        # Basic permission checking (expand based on roles)
        if channel.startswith("user_") and not channel.endswith(connection.user_id):
            return False  # Can't subscribe to other users' private channels

        if channel == Channel.COMMAND and connection.user_role not in [
            "task_force_leader",
            "operations_chief",
        ]:
            return False  # Command channel restricted

        return True

    async def _heartbeat_task(self):
        """Background heartbeat monitoring task."""
        while self.running:
            try:
                now = datetime.now(UTC)
                timeout_threshold = now - timedelta(minutes=2)  # 2 minute timeout

                # Check for stale connections
                stale_connections = []
                for connection in self.connections.values():
                    if connection.last_heartbeat < timeout_threshold:
                        stale_connections.append(connection.id)

                # Remove stale connections
                for connection_id in stale_connections:
                    if connection_id in self.connections:
                        await self.connections[connection_id].close(
                            1001, "Connection timeout"
                        )
                        self.remove_connection(connection_id)

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Heartbeat task error: {str(e)}")
                await asyncio.sleep(30)

    async def _cleanup_task(self):
        """Background cleanup task."""
        while self.running:
            try:
                # Clean up expired messages
                if self.redis_client:
                    # This would implement message expiration cleanup
                    pass

                await asyncio.sleep(300)  # Clean every 5 minutes

            except Exception as e:
                logger.error(f"Cleanup task error: {str(e)}")
                await asyncio.sleep(300)

    async def _redis_subscriber_task(self):
        """Redis subscriber task for clustering."""
        if not self.redis_client:
            return

        pubsub = self.redis_client.pubsub()
        await pubsub.psubscribe("channel:*")

        try:
            async for redis_message in pubsub.listen():
                if redis_message["type"] == "pmessage":
                    try:
                        data = json.loads(redis_message["data"])
                        message = Message.from_dict(data)
                        await self._deliver_local_message(message)
                    except Exception as e:
                        logger.error(f"Redis message processing error: {str(e)}")

        except Exception as e:
            logger.error(f"Redis subscriber error: {str(e)}")

    def add_message_handler(self, message_type: MessageType, handler: Callable):
        """Add message handler.

        Args:
            message_type: Message type to handle
            handler: Handler function
        """
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)

    def get_connection_stats(self) -> dict[str, Any]:
        """Get connection statistics.

        Returns:
            Connection statistics
        """
        now = datetime.now(UTC)
        active_connections = sum(
            1 for conn in self.connections.values() if conn.is_alive()
        )

        role_distribution = {}
        for conn in self.connections.values():
            role = conn.user_role
            role_distribution[role] = role_distribution.get(role, 0) + 1

        return {
            "total_connections": len(self.connections),
            "active_connections": active_connections,
            "channels": len(self.channel_manager.subscriptions),
            "role_distribution": role_distribution,
            "timestamp": now.isoformat(),
        }


# WebSocket handler
async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    """WebSocket connection handler.

    Args:
        request: HTTP request

    Returns:
        WebSocket response
    """
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)

    # Get message broker from app
    broker: MessageBroker = request.app["message_broker"]

    # Create connection (authentication would happen here in production)
    user_id = request.headers.get("X-User-ID", "anonymous")
    user_role = request.headers.get("X-User-Role", "observer")

    connection = WebSocketConnection(ws, user_id, user_role)
    broker.add_connection(connection)

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                await broker.handle_websocket_message(connection, msg.data)
            elif msg.type == WSMsgType.ERROR:
                logger.error(f"WebSocket error: {ws.exception()}")
                break
    except Exception as e:
        logger.error(f"WebSocket handler error: {str(e)}")
    finally:
        broker.remove_connection(connection.id)

    return ws


# Notification helpers
async def send_safety_alert(
    broker: MessageBroker,
    task_force_id: str,
    alert_data: dict[str, Any],
    sender: str = "system",
):
    """Send safety alert.

    Args:
        broker: Message broker
        task_force_id: Task force identifier
        alert_data: Alert data
        sender: Alert sender
    """
    message = Message(
        id=str(uuid.uuid4()),
        type=MessageType.SAFETY_ALERT,
        channel=Channel.task_force(task_force_id),
        sender=sender,
        recipient=None,
        content=alert_data,
        priority=Priority.CRITICAL,
        timestamp=datetime.now(UTC),
        requires_ack=True,
    )

    await broker.publish_message(message)

    # Also send to safety channel
    safety_message = Message(
        id=str(uuid.uuid4()),
        type=MessageType.SAFETY_ALERT,
        channel=Channel.SAFETY,
        sender=sender,
        recipient=None,
        content=alert_data,
        priority=Priority.CRITICAL,
        timestamp=datetime.now(UTC),
        requires_ack=True,
    )

    await broker.publish_message(safety_message)


async def send_deployment_update(
    broker: MessageBroker,
    deployment_id: str,
    update_data: dict[str, Any],
    sender: str = "system",
):
    """Send deployment update.

    Args:
        broker: Message broker
        deployment_id: Deployment identifier
        update_data: Update data
        sender: Update sender
    """
    message = Message(
        id=str(uuid.uuid4()),
        type=MessageType.DEPLOYMENT_UPDATE,
        channel=Channel.deployment(deployment_id),
        sender=sender,
        recipient=None,
        content=update_data,
        priority=Priority.HIGH,
        timestamp=datetime.now(UTC),
        requires_ack=False,
    )

    await broker.publish_message(message)


async def send_personnel_notification(
    broker: MessageBroker,
    user_id: str,
    notification_data: dict[str, Any],
    priority: Priority = Priority.NORMAL,
    sender: str = "system",
):
    """Send notification to specific user.

    Args:
        broker: Message broker
        user_id: User identifier
        notification_data: Notification data
        priority: Message priority
        sender: Notification sender
    """
    message = Message(
        id=str(uuid.uuid4()),
        type=MessageType.NOTIFICATION,
        channel=Channel.private(user_id),
        sender=sender,
        recipient=user_id,
        content=notification_data,
        priority=priority,
        timestamp=datetime.now(UTC),
        requires_ack=False,
    )

    await broker.publish_message(message)


# Factory function
def create_communication_system(redis_url: str | None = None) -> MessageBroker:
    """Create real-time communication system.

    Args:
        redis_url: Redis URL for clustering support

    Returns:
        Configured message broker
    """
    return MessageBroker(redis_url)
