"""Performance optimization and caching layer for FEMA USAR MCP Server."""

import hashlib
import json
import logging
import threading
import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    data: Any
    timestamp: datetime
    ttl_seconds: int
    access_count: int = 0
    last_accessed: datetime = None

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


class DistributedCache:
    """High-performance distributed cache with TTL and eviction policies."""

    def __init__(self, max_size: int = 10000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._access_order: list[str] = []
        self._lock = threading.RLock()

        # Performance metrics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

        # Start background cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_expired, daemon=True
        )
        self._cleanup_thread.start()

    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function name and arguments."""
        key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _evict_lru(self) -> None:
        """Evict least recently used items."""
        while len(self._cache) >= self.max_size:
            if not self._access_order:
                break
            lru_key = self._access_order.pop(0)
            if lru_key in self._cache:
                del self._cache[lru_key]
                self.evictions += 1

    def _cleanup_expired(self) -> None:
        """Background thread to clean up expired entries."""
        while True:
            try:
                time.sleep(60)  # Check every minute
                with self._lock:
                    expired_keys = [
                        key for key, entry in self._cache.items() if entry.is_expired()
                    ]
                    for key in expired_keys:
                        del self._cache[key]
                        if key in self._access_order:
                            self._access_order.remove(key)
                        self.evictions += 1
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")

    def get(self, key: str) -> Any | None:
        """Get item from cache."""
        with self._lock:
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

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set item in cache."""
        with self._lock:
            ttl = ttl or self.default_ttl

            # Evict if necessary
            if len(self._cache) >= self.max_size:
                self._evict_lru()

            entry = CacheEntry(data=value, timestamp=datetime.now(), ttl_seconds=ttl)

            self._cache[key] = entry

            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

    def invalidate(self, pattern: str | None = None) -> int:
        """Invalidate cache entries matching pattern."""
        with self._lock:
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

    def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        with self._lock:
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


# Global cache instance
_cache = DistributedCache()


def cached(ttl: int = 3600, cache_instance: DistributedCache | None = None):
    """Decorator for caching function results with TTL."""

    def decorator(func: Callable) -> Callable:
        cache = cache_instance or _cache

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache._generate_key(func.__name__, args, kwargs)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result

            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing function")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


class AsyncTaskManager:
    """Manages asynchronous task execution for improved performance."""

    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks: dict[str, Future] = {}
        self._lock = threading.Lock()

    def submit_task(self, task_id: str, func: Callable, *args, **kwargs) -> Future:
        """Submit task for asynchronous execution."""
        with self._lock:
            future = self.executor.submit(func, *args, **kwargs)
            self.active_tasks[task_id] = future

            # Clean up completed tasks
            def cleanup_task(f):
                with self._lock:
                    if task_id in self.active_tasks:
                        del self.active_tasks[task_id]

            future.add_done_callback(cleanup_task)
            return future

    def get_task_status(self, task_id: str) -> str | None:
        """Get status of a task."""
        with self._lock:
            if task_id not in self.active_tasks:
                return None

            future = self.active_tasks[task_id]
            if future.done():
                if future.cancelled():
                    return "cancelled"
                elif future.exception():
                    return "failed"
                else:
                    return "completed"
            else:
                return "running"

    def get_task_result(self, task_id: str, timeout: float | None = None) -> Any:
        """Get result of a task."""
        with self._lock:
            if task_id not in self.active_tasks:
                raise ValueError(f"Task {task_id} not found")

            future = self.active_tasks[task_id]
            return future.result(timeout=timeout)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        with self._lock:
            if task_id not in self.active_tasks:
                return False

            future = self.active_tasks[task_id]
            return future.cancel()

    def get_active_tasks(self) -> list[str]:
        """Get list of active task IDs."""
        with self._lock:
            return list(self.active_tasks.keys())

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the task manager."""
        self.executor.shutdown(wait=wait)


# Global task manager
_task_manager = AsyncTaskManager()


class PerformanceMonitor:
    """Monitors and reports on system performance metrics."""

    def __init__(self):
        self.metrics: dict[str, list[float]] = {}
        self.counters: dict[str, int] = {}
        self._lock = threading.Lock()

    def record_metric(self, name: str, value: float) -> None:
        """Record a performance metric."""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = []

            self.metrics[name].append(value)

            # Keep only last 1000 values
            if len(self.metrics[name]) > 1000:
                self.metrics[name] = self.metrics[name][-1000:]

    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter."""
        with self._lock:
            self.counters[name] = self.counters.get(name, 0) + value

    def get_metric_stats(self, name: str) -> dict[str, float] | None:
        """Get statistics for a metric."""
        with self._lock:
            if name not in self.metrics or not self.metrics[name]:
                return None

            values = self.metrics[name]
            return {
                "count": len(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "latest": values[-1] if values else 0,
            }

    def get_all_stats(self) -> dict[str, Any]:
        """Get all performance statistics."""
        with self._lock:
            stats = {
                "metrics": {},
                "counters": self.counters.copy(),
                "timestamp": datetime.now().isoformat(),
            }

            for name in self.metrics:
                stats["metrics"][name] = self.get_metric_stats(name)

            return stats

    def reset_metrics(self) -> None:
        """Reset all metrics and counters."""
        with self._lock:
            self.metrics.clear()
            self.counters.clear()


# Global performance monitor
_perf_monitor = PerformanceMonitor()


def performance_monitor(metric_name: str | None = None):
    """Decorator to monitor function performance."""

    def decorator(func: Callable) -> Callable:
        name = metric_name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                _perf_monitor.increment_counter(f"{name}.success")
                return result
            except Exception:
                _perf_monitor.increment_counter(f"{name}.error")
                raise
            finally:
                execution_time = time.time() - start_time
                _perf_monitor.record_metric(f"{name}.execution_time", execution_time)
                _perf_monitor.increment_counter(f"{name}.calls")

        return wrapper

    return decorator


class DataCompressor:
    """Handles data compression for improved performance."""

    @staticmethod
    def compress_json(data: dict[str, Any]) -> str:
        """Compress JSON data for storage/transmission."""
        import base64
        import gzip

        json_str = json.dumps(data, separators=(",", ":"))
        compressed = gzip.compress(json_str.encode())
        return base64.b64encode(compressed).decode()

    @staticmethod
    def decompress_json(compressed_data: str) -> dict[str, Any]:
        """Decompress JSON data."""
        import base64
        import gzip

        compressed = base64.b64decode(compressed_data.encode())
        decompressed = gzip.decompress(compressed)
        return json.loads(decompressed.decode())


class BatchProcessor:
    """Handles batch processing of operations for improved efficiency."""

    def __init__(self, batch_size: int = 100, flush_interval: float = 5.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.batches: dict[str, list[Any]] = {}
        self.processors: dict[str, Callable] = {}
        self._lock = threading.Lock()

        # Start flush timer
        self._timer = threading.Timer(self.flush_interval, self._flush_all_batches)
        self._timer.daemon = True
        self._timer.start()

    def register_processor(self, batch_type: str, processor: Callable) -> None:
        """Register a processor for a batch type."""
        with self._lock:
            self.processors[batch_type] = processor
            if batch_type not in self.batches:
                self.batches[batch_type] = []

    def add_to_batch(self, batch_type: str, item: Any) -> None:
        """Add item to batch."""
        with self._lock:
            if batch_type not in self.batches:
                self.batches[batch_type] = []

            self.batches[batch_type].append(item)

            # Flush if batch is full
            if len(self.batches[batch_type]) >= self.batch_size:
                self._flush_batch(batch_type)

    def _flush_batch(self, batch_type: str) -> None:
        """Flush a specific batch."""
        if batch_type in self.batches and self.batches[batch_type]:
            if batch_type in self.processors:
                items = self.batches[batch_type].copy()
                self.batches[batch_type].clear()

                try:
                    self.processors[batch_type](items)
                except Exception as e:
                    logger.error(f"Batch processing error for {batch_type}: {e}")

    def _flush_all_batches(self) -> None:
        """Flush all batches."""
        with self._lock:
            for batch_type in list(self.batches.keys()):
                self._flush_batch(batch_type)

        # Restart timer
        self._timer = threading.Timer(self.flush_interval, self._flush_all_batches)
        self._timer.daemon = True
        self._timer.start()

    def flush_now(self, batch_type: str | None = None) -> None:
        """Flush batches immediately."""
        with self._lock:
            if batch_type:
                self._flush_batch(batch_type)
            else:
                for bt in list(self.batches.keys()):
                    self._flush_batch(bt)


# Global batch processor
_batch_processor = BatchProcessor()


def get_cache_stats() -> dict[str, Any]:
    """Get global cache statistics."""
    return _cache.get_stats()


def get_performance_stats() -> dict[str, Any]:
    """Get global performance statistics."""
    stats = _perf_monitor.get_all_stats()
    stats["cache"] = get_cache_stats()
    stats["active_tasks"] = len(_task_manager.get_active_tasks())
    return stats


def clear_cache(pattern: str | None = None) -> int:
    """Clear cache entries."""
    return _cache.invalidate(pattern)


def submit_async_task(task_id: str, func: Callable, *args, **kwargs) -> Future:
    """Submit asynchronous task."""
    return _task_manager.submit_task(task_id, func, *args, **kwargs)


def get_async_task_status(task_id: str) -> str | None:
    """Get async task status."""
    return _task_manager.get_task_status(task_id)


def get_async_task_result(task_id: str, timeout: float | None = None) -> Any:
    """Get async task result."""
    return _task_manager.get_task_result(task_id, timeout)


# Pre-configured cache decorators for common use cases
cache_short = cached(ttl=300)  # 5 minutes
cache_medium = cached(ttl=1800)  # 30 minutes
cache_long = cached(ttl=3600)  # 1 hour
cache_extended = cached(ttl=14400)  # 4 hours


def optimize_tool_response(func: Callable) -> Callable:
    """Decorator that combines caching and performance monitoring for tool functions."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Start performance monitoring
        start_time = time.time()

        try:
            # Check for cached result
            cache_key = _cache._generate_key(func.__name__, args, kwargs)
            cached_result = _cache.get(cache_key)

            if cached_result is not None:
                _perf_monitor.increment_counter(f"{func.__name__}.cache_hit")
                _perf_monitor.record_metric(
                    f"{func.__name__}.response_time", time.time() - start_time
                )
                return cached_result

            # Execute function
            result = func(*args, **kwargs)

            # Cache result with appropriate TTL based on function type
            ttl = 300  # Default 5 minutes
            if "status" in func.__name__ or "monitor" in func.__name__:
                ttl = 60  # 1 minute for status/monitoring
            elif "calculation" in func.__name__ or "analysis" in func.__name__:
                ttl = 900  # 15 minutes for calculations
            elif "configuration" in func.__name__ or "setup" in func.__name__:
                ttl = 1800  # 30 minutes for configuration

            _cache.set(cache_key, result, ttl)

            # Record performance metrics
            _perf_monitor.increment_counter(f"{func.__name__}.cache_miss")
            _perf_monitor.increment_counter(f"{func.__name__}.execution")
            _perf_monitor.record_metric(
                f"{func.__name__}.response_time", time.time() - start_time
            )

            return result

        except Exception:
            _perf_monitor.increment_counter(f"{func.__name__}.error")
            raise

    return wrapper


class ConnectionPool:
    """Connection pool for external service connections."""

    def __init__(self, max_connections: int = 20):
        self.max_connections = max_connections
        self.connections: list[Any] = []
        self.in_use: set = set()
        self._lock = threading.Lock()

    def get_connection(self) -> Any:
        """Get connection from pool."""
        with self._lock:
            if self.connections:
                conn = self.connections.pop()
                self.in_use.add(id(conn))
                return conn
            elif len(self.in_use) < self.max_connections:
                # Create new connection (placeholder)
                conn = {"id": len(self.in_use), "created": datetime.now()}
                self.in_use.add(id(conn))
                return conn
            else:
                raise Exception("Connection pool exhausted")

    def return_connection(self, conn: Any) -> None:
        """Return connection to pool."""
        with self._lock:
            if id(conn) in self.in_use:
                self.in_use.remove(id(conn))
                self.connections.append(conn)

    def close_all(self) -> None:
        """Close all connections."""
        with self._lock:
            self.connections.clear()
            self.in_use.clear()


# Global connection pool
_connection_pool = ConnectionPool()


def performance_optimized_tool(
    cache_ttl: int = 300, enable_monitoring: bool = True, enable_async: bool = False
):
    """Comprehensive performance optimization decorator for tools."""

    def decorator(func: Callable) -> Callable:
        # Apply caching
        cached_func = cached(ttl=cache_ttl)(func)

        # Apply performance monitoring
        if enable_monitoring:
            cached_func = performance_monitor()(cached_func)

        if enable_async:

            @wraps(cached_func)
            def async_wrapper(*args, **kwargs):
                task_id = f"{func.__name__}_{int(time.time() * 1000)}"
                _task_manager.submit_task(task_id, cached_func, *args, **kwargs)

                # For async mode, return task ID instead of result
                return json.dumps(
                    {
                        "tool": func.__name__,
                        "status": "async_submitted",
                        "task_id": task_id,
                        "message": "Task submitted for asynchronous processing",
                    },
                    indent=2,
                )

            return async_wrapper

        return cached_func

    return decorator
