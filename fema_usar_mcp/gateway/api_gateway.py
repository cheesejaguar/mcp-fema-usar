"""API Gateway and load balancing for FEMA USAR MCP.

Provides intelligent routing, load balancing, circuit breaking,
and API management capabilities for USAR operations.
"""

import asyncio
import hashlib
import logging
import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import aiohttp
import yarl
from aiohttp import ClientError, ClientSession, ClientTimeout, web

logger = logging.getLogger(__name__)


class LoadBalanceStrategy(Enum):
    """Load balancing strategies."""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    HASH_BASED = "hash_based"
    HEALTH_WEIGHTED = "health_weighted"


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class BackendServer:
    """Backend server configuration."""

    id: str
    host: str
    port: int
    weight: int = 1
    max_connections: int = 100
    timeout: float = 30.0
    health_check_url: str = "/health"
    enabled: bool = True

    # Runtime state
    active_connections: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    last_health_check: datetime | None = None
    health_status: str = "unknown"  # healthy, unhealthy, unknown
    response_times: list[float] = None

    def __post_init__(self):
        if self.response_times is None:
            self.response_times = []

    @property
    def url(self) -> str:
        """Get server base URL."""
        return f"http://{self.host}:{self.port}"

    @property
    def avg_response_time(self) -> float:
        """Get average response time."""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times[-100:])  # Last 100 requests

    @property
    def error_rate(self) -> float:
        """Get error rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100

    def is_healthy(self) -> bool:
        """Check if server is healthy."""
        return (
            self.enabled
            and self.health_status == "healthy"
            and self.active_connections < self.max_connections
        )


@dataclass
class CircuitBreaker:
    """Circuit breaker for backend protection."""

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 3

    # State
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None

    def can_execute(self) -> bool:
        """Check if requests can be executed."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time and datetime.now(
                UTC
            ) - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                return True
            return False
        else:  # HALF_OPEN
            return True

    def record_success(self):
        """Record successful request."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0

    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.now(UTC)

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class LoadBalancer:
    """Intelligent load balancer for backend servers."""

    def __init__(
        self, strategy: LoadBalanceStrategy = LoadBalanceStrategy.HEALTH_WEIGHTED
    ):
        """Initialize load balancer.

        Args:
            strategy: Load balancing strategy
        """
        self.strategy = strategy
        self.servers: list[BackendServer] = []
        self.current_index = 0

    def add_server(self, server: BackendServer):
        """Add backend server.

        Args:
            server: Backend server to add
        """
        self.servers.append(server)
        logger.info(f"Added backend server: {server.id} ({server.url})")

    def remove_server(self, server_id: str):
        """Remove backend server.

        Args:
            server_id: Server ID to remove
        """
        self.servers = [s for s in self.servers if s.id != server_id]
        logger.info(f"Removed backend server: {server_id}")

    def get_healthy_servers(self) -> list[BackendServer]:
        """Get list of healthy servers.

        Returns:
            List of healthy backend servers
        """
        return [s for s in self.servers if s.is_healthy()]

    def select_server(
        self, request_data: dict[str, Any] = None
    ) -> BackendServer | None:
        """Select backend server based on strategy.

        Args:
            request_data: Request data for hash-based routing

        Returns:
            Selected backend server or None
        """
        healthy_servers = self.get_healthy_servers()
        if not healthy_servers:
            return None

        if self.strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._round_robin_select(healthy_servers)
        elif self.strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(healthy_servers)
        elif self.strategy == LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(healthy_servers)
        elif self.strategy == LoadBalanceStrategy.HASH_BASED:
            return self._hash_based_select(healthy_servers, request_data)
        elif self.strategy == LoadBalanceStrategy.HEALTH_WEIGHTED:
            return self._health_weighted_select(healthy_servers)
        else:
            return healthy_servers[0]  # Fallback

    def _round_robin_select(self, servers: list[BackendServer]) -> BackendServer:
        """Round-robin server selection."""
        server = servers[self.current_index % len(servers)]
        self.current_index += 1
        return server

    def _least_connections_select(self, servers: list[BackendServer]) -> BackendServer:
        """Least connections server selection."""
        return min(servers, key=lambda s: s.active_connections)

    def _weighted_round_robin_select(
        self, servers: list[BackendServer]
    ) -> BackendServer:
        """Weighted round-robin server selection."""
        # Simple implementation - expand by weight
        weighted_servers = []
        for server in servers:
            weighted_servers.extend([server] * server.weight)

        if weighted_servers:
            server = weighted_servers[self.current_index % len(weighted_servers)]
            self.current_index += 1
            return server
        return servers[0]

    def _hash_based_select(
        self, servers: list[BackendServer], request_data: dict[str, Any]
    ) -> BackendServer:
        """Hash-based server selection."""
        if not request_data:
            return servers[0]

        # Use user ID or IP for consistent hashing
        hash_key = request_data.get("user_id") or request_data.get(
            "client_ip", "default"
        )
        hash_value = hashlib.md5(hash_key.encode()).hexdigest()
        index = int(hash_value, 16) % len(servers)
        return servers[index]

    def _health_weighted_select(self, servers: list[BackendServer]) -> BackendServer:
        """Health-weighted server selection."""

        # Score based on response time, error rate, and connections
        def calculate_score(server: BackendServer) -> float:
            base_score = 100.0

            # Penalize high response times
            if server.avg_response_time > 0:
                base_score -= min(server.avg_response_time * 10, 50)

            # Penalize high error rates
            base_score -= min(server.error_rate, 40)

            # Penalize high connection usage
            connection_usage = (
                server.active_connections / server.max_connections
            ) * 100
            base_score -= min(connection_usage, 30)

            return max(base_score, 1.0)  # Minimum score of 1

        # Select server with highest score
        return max(servers, key=calculate_score)


class RateLimiter:
    """Rate limiting functionality."""

    def __init__(self, max_requests: int = 100, time_window: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests per time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: dict[str, list[float]] = {}

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed.

        Args:
            identifier: Client identifier (IP, user ID, etc.)

        Returns:
            True if request is allowed
        """
        now = time.time()

        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time
                for req_time in self.requests[identifier]
                if now - req_time < self.time_window
            ]
        else:
            self.requests[identifier] = []

        # Check limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False

        # Add current request
        self.requests[identifier].append(now)
        return True

    def get_reset_time(self, identifier: str) -> float | None:
        """Get rate limit reset time.

        Args:
            identifier: Client identifier

        Returns:
            Reset time timestamp or None
        """
        if identifier not in self.requests or not self.requests[identifier]:
            return None

        oldest_request = min(self.requests[identifier])
        return oldest_request + self.time_window


class APIGateway:
    """Main API Gateway implementation."""

    def __init__(
        self,
        load_balancer: LoadBalancer,
        rate_limiter: RateLimiter | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        """Initialize API Gateway.

        Args:
            load_balancer: Load balancer instance
            rate_limiter: Rate limiter instance
            circuit_breaker: Circuit breaker instance
        """
        self.load_balancer = load_balancer
        self.rate_limiter = rate_limiter
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.session: ClientSession | None = None

        # Metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0

    async def initialize(self):
        """Initialize gateway resources."""
        timeout = ClientTimeout(total=30, connect=10)
        self.session = ClientSession(
            timeout=timeout,
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=30),
        )

        # Start health check task
        asyncio.create_task(self._health_check_loop())
        logger.info("API Gateway initialized")

    async def shutdown(self):
        """Shutdown gateway resources."""
        if self.session:
            await self.session.close()
        logger.info("API Gateway shutdown")

    async def handle_request(self, request: web.Request) -> web.Response:
        """Handle incoming request.

        Args:
            request: Incoming HTTP request

        Returns:
            HTTP response
        """
        start_time = time.time()
        self.total_requests += 1

        try:
            # Rate limiting check
            if self.rate_limiter:
                client_ip = request.remote or "unknown"
                if not self.rate_limiter.is_allowed(client_ip):
                    reset_time = self.rate_limiter.get_reset_time(client_ip)
                    headers = {}
                    if reset_time:
                        headers["X-RateLimit-Reset"] = str(int(reset_time))
                    return web.Response(
                        status=429, text="Rate limit exceeded", headers=headers
                    )

            # Circuit breaker check
            if not self.circuit_breaker.can_execute():
                return web.Response(status=503, text="Service temporarily unavailable")

            # Select backend server
            request_data = {
                "client_ip": request.remote,
                "user_id": request.headers.get("X-User-ID"),
            }
            server = self.load_balancer.select_server(request_data)

            if not server:
                return web.Response(
                    status=503, text="No healthy backend servers available"
                )

            # Forward request
            response = await self._forward_request(request, server)

            # Update metrics
            response_time = time.time() - start_time
            server.response_times.append(response_time)
            server.total_requests += 1
            self.total_response_time += response_time
            self.successful_requests += 1
            self.circuit_breaker.record_success()

            return response

        except Exception as e:
            # Update failure metrics
            response_time = time.time() - start_time
            self.total_response_time += response_time
            self.failed_requests += 1
            self.circuit_breaker.record_failure()

            logger.error(f"Gateway request failed: {str(e)}")
            return web.Response(status=502, text="Bad Gateway")

    async def _forward_request(
        self, request: web.Request, server: BackendServer
    ) -> web.Response:
        """Forward request to backend server.

        Args:
            request: Original request
            server: Target backend server

        Returns:
            Backend response
        """
        # Increment active connections
        server.active_connections += 1

        try:
            # Build target URL
            target_url = yarl.URL(server.url) / request.path_qs.lstrip("/")

            # Prepare headers
            headers = dict(request.headers)
            headers["X-Forwarded-For"] = request.remote or "unknown"
            headers["X-Forwarded-Proto"] = "https"
            headers["X-Gateway-Server"] = server.id

            # Remove hop-by-hop headers
            hop_headers = {
                "connection",
                "keep-alive",
                "proxy-authenticate",
                "proxy-authorization",
                "te",
                "trailers",
                "transfer-encoding",
                "upgrade",
            }
            for header in hop_headers:
                headers.pop(header, None)

            # Forward request
            async with self.session.request(
                method=request.method,
                url=str(target_url),
                headers=headers,
                data=await request.read() if request.can_read_body else None,
                allow_redirects=False,
            ) as backend_response:
                # Read response body
                body = await backend_response.read()

                # Prepare response headers
                response_headers = dict(backend_response.headers)

                # Remove hop-by-hop headers from response
                for header in hop_headers:
                    response_headers.pop(header, None)

                # Add gateway headers
                response_headers["X-Gateway-Server"] = server.id
                response_headers["X-Response-Time"] = str(time.time())

                return web.Response(
                    status=backend_response.status, headers=response_headers, body=body
                )

        except ClientError as e:
            server.failed_requests += 1
            raise Exception(f"Backend request failed: {str(e)}") from e
        finally:
            # Decrement active connections
            server.active_connections = max(0, server.active_connections - 1)

    async def _health_check_loop(self):
        """Health check loop for backend servers."""
        while True:
            try:
                await self._check_server_health()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
                await asyncio.sleep(30)

    async def _check_server_health(self):
        """Check health of all backend servers."""
        for server in self.load_balancer.servers:
            try:
                health_url = f"{server.url}{server.health_check_url}"

                async with self.session.get(health_url, timeout=10) as response:
                    if response.status == 200:
                        server.health_status = "healthy"
                    else:
                        server.health_status = "unhealthy"

                server.last_health_check = datetime.now(UTC)

            except Exception as e:
                server.health_status = "unhealthy"
                server.last_health_check = datetime.now(UTC)
                logger.warning(f"Health check failed for {server.id}: {str(e)}")

    def get_metrics(self) -> dict[str, Any]:
        """Get gateway metrics.

        Returns:
            Gateway metrics
        """
        avg_response_time = 0.0
        if self.total_requests > 0:
            avg_response_time = self.total_response_time / self.total_requests

        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (
                (self.successful_requests / self.total_requests * 100)
                if self.total_requests > 0
                else 0
            ),
            "average_response_time": avg_response_time,
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "backend_servers": [
                {
                    "id": server.id,
                    "url": server.url,
                    "health_status": server.health_status,
                    "active_connections": server.active_connections,
                    "total_requests": server.total_requests,
                    "error_rate": server.error_rate,
                    "avg_response_time": server.avg_response_time,
                }
                for server in self.load_balancer.servers
            ],
        }


# Middleware for request logging and metrics
async def logging_middleware(request: web.Request, handler: Callable) -> web.Response:
    """Logging middleware for requests."""
    start_time = time.time()

    try:
        response = await handler(request)

        # Log successful request
        logger.info(
            f"{request.method} {request.path} - {response.status} - "
            f"{time.time() - start_time:.3f}s"
        )

        return response

    except Exception as e:
        # Log failed request
        logger.error(
            f"{request.method} {request.path} - ERROR - "
            f"{time.time() - start_time:.3f}s - {str(e)}"
        )
        raise


# Factory function for creating API Gateway
def create_api_gateway(
    backend_servers: list[dict[str, Any]],
    strategy: LoadBalanceStrategy = LoadBalanceStrategy.HEALTH_WEIGHTED,
    rate_limit: dict[str, int] | None = None,
) -> APIGateway:
    """Create configured API Gateway.

    Args:
        backend_servers: List of backend server configurations
        strategy: Load balancing strategy
        rate_limit: Rate limiting configuration

    Returns:
        Configured API Gateway
    """
    # Create load balancer
    load_balancer = LoadBalancer(strategy)

    # Add backend servers
    for server_config in backend_servers:
        server = BackendServer(**server_config)
        load_balancer.add_server(server)

    # Create rate limiter if configured
    rate_limiter = None
    if rate_limit:
        rate_limiter = RateLimiter(
            max_requests=rate_limit.get("max_requests", 100),
            time_window=rate_limit.get("time_window", 60),
        )

    # Create circuit breaker
    circuit_breaker = CircuitBreaker()

    return APIGateway(load_balancer, rate_limiter, circuit_breaker)
