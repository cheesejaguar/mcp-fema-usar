"""Native async performance utilities for FEMA USAR MCP Server.

This module provides asyncio-native implementations of caching, task management,
and performance monitoring, replacing ThreadPoolExecutor patterns with native async.
"""

import asyncio
import hashlib
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AsyncCacheEntry:
    """Cache entry for async operations."""

    data: Any
    timestamp: datetime
    ttl_seconds: int
    access_count: int = 0
    last_accessed: datetime | None = None

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl_seconds)

    def access(self) -> Any:
        """Access cache entry and update metadata."""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.data


class AsyncDistributedCache:
    """Async-safe cache with asyncio.Lock for thread safety."""

    def __init__(self, max_size: int = 10000, default_ttl: int = 3600):
        """Initialize the async cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict[str, AsyncCacheEntry] = {}
        self._access_order: list[str] = []
        self._lock = asyncio.Lock()

        # Performance metrics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

        # Cleanup task handle
        self._cleanup_task: asyncio.Task | None = None

    async def start_cleanup(self) -> None:
        """Start the background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())

    async def stop_cleanup(self) -> None:
        """Stop the background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function name and arguments."""
        key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def _evict_lru(self) -> None:
        """Evict least recently used items (must be called with lock held)."""
        while len(self._cache) >= self.max_size:
            if not self._access_order:
                break
            lru_key = self._access_order.pop(0)
            if lru_key in self._cache:
                del self._cache[lru_key]
                self.evictions += 1

    async def _cleanup_expired(self) -> None:
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                async with self._lock:
                    expired_keys = [
                        key for key, entry in self._cache.items() if entry.is_expired()
                    ]
                    for key in expired_keys:
                        del self._cache[key]
                        if key in self._access_order:
                            self._access_order.remove(key)
                        self.evictions += 1

                    if expired_keys:
                        logger.debug(
                            f"Cleaned up {len(expired_keys)} expired cache entries"
                        )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Async cache cleanup error: {e}")

    async def get(self, key: str) -> Any | None:
        """Get item from cache."""
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    # Update access order
                    if key in self._access_order:
                        self._access_order.remove(key)
                    self._access_order.append(key)
                    self.hits += 1
                    return entry.access()
                else:
                    del self._cache[key]
                    if key in self._access_order:
                        self._access_order.remove(key)

            self.misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set item in cache."""
        async with self._lock:
            ttl = ttl or self.default_ttl

            # Evict if necessary
            if len(self._cache) >= self.max_size:
                await self._evict_lru()

            entry = AsyncCacheEntry(
                data=value, timestamp=datetime.now(), ttl_seconds=ttl
            )
            self._cache[key] = entry

            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

    async def invalidate(self, pattern: str | None = None) -> int:
        """Invalidate cache entries matching pattern."""
        async with self._lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                self._access_order.clear()
                return count

            keys_to_remove = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)

            return len(keys_to_remove)

    async def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        async with self._lock:
            hit_rate = (
                self.hits / (self.hits + self.misses)
                if (self.hits + self.misses) > 0
                else 0
            )
            return {
                "cache_size": len(self._cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "hit_rate": round(hit_rate, 3),
                "memory_usage_mb": sum(
                    len(str(entry.data)) for entry in self._cache.values()
                )
                / 1024
                / 1024,
            }


@dataclass
class AsyncTaskInfo:
    """Information about an async task."""

    task_id: str
    task: asyncio.Task
    created_at: datetime
    func_name: str
    status: str = "running"
    result: Any = None
    error: str | None = None


class AsyncTaskManager:
    """Native asyncio task management."""

    def __init__(self, max_concurrent: int = 100):
        """Initialize the async task manager.

        Args:
            max_concurrent: Maximum concurrent tasks
        """
        self.max_concurrent = max_concurrent
        self._tasks: dict[str, AsyncTaskInfo] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._lock = asyncio.Lock()

    async def submit_task(
        self, task_id: str, coro: Callable, *args, **kwargs
    ) -> asyncio.Task:
        """Submit a coroutine for async execution.

        Args:
            task_id: Unique task identifier
            coro: Coroutine function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The created asyncio.Task
        """

        async def task_wrapper():
            async with self._semaphore:
                try:
                    result = await coro(*args, **kwargs)
                    async with self._lock:
                        if task_id in self._tasks:
                            self._tasks[task_id].status = "completed"
                            self._tasks[task_id].result = result
                    return result
                except Exception as e:
                    async with self._lock:
                        if task_id in self._tasks:
                            self._tasks[task_id].status = "failed"
                            self._tasks[task_id].error = str(e)
                    raise

        task = asyncio.create_task(task_wrapper())

        async with self._lock:
            self._tasks[task_id] = AsyncTaskInfo(
                task_id=task_id,
                task=task,
                created_at=datetime.now(),
                func_name=coro.__name__ if hasattr(coro, "__name__") else "unknown",
            )

        return task

    async def get_task_status(self, task_id: str) -> str | None:
        """Get status of a task."""
        async with self._lock:
            if task_id not in self._tasks:
                return None

            task_info = self._tasks[task_id]
            if task_info.task.done():
                if task_info.task.cancelled():
                    return "cancelled"
                elif task_info.task.exception():
                    return "failed"
                else:
                    return "completed"
            return "running"

    async def get_task_result(self, task_id: str, timeout: float | None = None) -> Any:
        """Get result of a task."""
        async with self._lock:
            if task_id not in self._tasks:
                raise ValueError(f"Task {task_id} not found")
            task = self._tasks[task_id].task

        return await asyncio.wait_for(task, timeout=timeout)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        async with self._lock:
            if task_id not in self._tasks:
                return False

            task = self._tasks[task_id].task
            return task.cancel()

    async def get_active_tasks(self) -> list[str]:
        """Get list of active task IDs."""
        async with self._lock:
            return [
                task_id for task_id, info in self._tasks.items() if not info.task.done()
            ]

    async def cleanup_completed(self, max_age_seconds: int = 3600) -> int:
        """Clean up old completed tasks.

        Args:
            max_age_seconds: Maximum age for completed tasks

        Returns:
            Number of tasks cleaned up
        """
        cutoff = datetime.now() - timedelta(seconds=max_age_seconds)
        async with self._lock:
            to_remove = [
                task_id
                for task_id, info in self._tasks.items()
                if info.task.done() and info.created_at < cutoff
            ]
            for task_id in to_remove:
                del self._tasks[task_id]
            return len(to_remove)

    async def get_stats(self) -> dict[str, Any]:
        """Get task manager statistics."""
        async with self._lock:
            running = sum(1 for info in self._tasks.values() if not info.task.done())
            completed = sum(
                1 for info in self._tasks.values() if info.status == "completed"
            )
            failed = sum(1 for info in self._tasks.values() if info.status == "failed")

            return {
                "total_tasks": len(self._tasks),
                "running": running,
                "completed": completed,
                "failed": failed,
                "max_concurrent": self.max_concurrent,
            }


def async_cached(ttl: int = 3600, cache: AsyncDistributedCache | None = None):
    """Decorator for caching async function results.

    Args:
        ttl: Time-to-live in seconds
        cache: Optional cache instance (creates new if not provided)

    Returns:
        Decorated async function
    """
    _cache = cache

    def decorator(func: Callable) -> Callable:
        # Create cache instance if not provided
        nonlocal _cache
        if _cache is None:
            _cache = AsyncDistributedCache()

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _cache._generate_key(func.__name__, args, kwargs)

            # Try to get from cache
            cached_result = await _cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Async cache hit for {func.__name__}")
                return cached_result

            # Execute function and cache result
            logger.debug(f"Async cache miss for {func.__name__}")
            result = await func(*args, **kwargs)
            await _cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def async_timed(func: Callable) -> Callable:
    """Decorator to measure async function execution time.

    Returns:
        Decorated async function that logs execution time
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            execution_time = (time.time() - start_time) * 1000
            logger.debug(f"{func.__name__} executed in {execution_time:.2f}ms")

    return wrapper


def async_retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for retrying async functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay

    Returns:
        Decorated async function with retry logic
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                            f"retrying in {current_delay}s: {e}"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )

            raise last_exception

        return wrapper

    return decorator


async def async_tool_wrapper(sync_func: Callable, *args, **kwargs) -> str:
    """Wrap a synchronous tool function for async execution.

    Args:
        sync_func: Synchronous function to wrap
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Tool result as string
    """
    return await asyncio.to_thread(sync_func, *args, **kwargs)


class AsyncRateLimiter:
    """Async-compatible rate limiter using token bucket algorithm."""

    def __init__(self, rate: float, capacity: float):
        """Initialize the rate limiter.

        Args:
            rate: Tokens added per second
            capacity: Maximum token capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> bool:
        """Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False if rate limited
        """
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def wait_for_token(self, tokens: float = 1.0) -> None:
        """Wait until tokens are available.

        Args:
            tokens: Number of tokens to acquire
        """
        while not await self.acquire(tokens):
            # Calculate wait time
            async with self._lock:
                wait_time = (tokens - self.tokens) / self.rate
            await asyncio.sleep(wait_time)


# Global async instances
_async_cache: AsyncDistributedCache | None = None
_async_task_manager: AsyncTaskManager | None = None


async def get_async_cache() -> AsyncDistributedCache:
    """Get or create the global async cache."""
    global _async_cache
    if _async_cache is None:
        _async_cache = AsyncDistributedCache()
        await _async_cache.start_cleanup()
    return _async_cache


async def get_async_task_manager() -> AsyncTaskManager:
    """Get or create the global async task manager."""
    global _async_task_manager
    if _async_task_manager is None:
        _async_task_manager = AsyncTaskManager()
    return _async_task_manager


async def get_async_performance_stats() -> dict[str, Any]:
    """Get async performance statistics."""
    cache = await get_async_cache()
    task_manager = await get_async_task_manager()

    return {
        "cache": await cache.get_stats(),
        "task_manager": await task_manager.get_stats(),
        "timestamp": datetime.now().isoformat(),
    }
