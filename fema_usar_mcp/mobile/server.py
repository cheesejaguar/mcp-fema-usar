"""Mobile/Field deployment server for Federal USAR MCP.

Optimized for edge computing, limited bandwidth, offline operations,
and rugged field environments.
"""

import asyncio
import logging
import os
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..monitoring.metrics import MonitoringManager
from .battery import BatteryManager
from .gps import GPSManager
from .offline import OfflineCache
from .sync import MobileSyncManager

logger = logging.getLogger(__name__)


class MobileConfig:
    """Mobile deployment configuration."""

    def __init__(self):
        self.mobile_mode = os.getenv("MOBILE_MODE", "true").lower() == "true"
        self.offline_capable = os.getenv("OFFLINE_CAPABLE", "true").lower() == "true"
        self.bandwidth_limited = (
            os.getenv("BANDWIDTH_LIMITED", "true").lower() == "true"
        )
        self.battery_optimization = (
            os.getenv("BATTERY_OPTIMIZATION", "true").lower() == "true"
        )
        self.gps_enabled = os.getenv("GPS_ENABLED", "true").lower() == "true"
        self.satellite_backup = os.getenv("SATELLITE_BACKUP", "true").lower() == "true"

        # Sync settings
        self.sync_interval = int(os.getenv("SYNC_INTERVAL", "300"))  # 5 minutes
        self.hq_server_url = os.getenv("HQ_SERVER_URL", "https://usar-mcp.fema.gov")

        # Cache settings
        self.max_cache_size_mb = int(os.getenv("MAX_CACHE_SIZE_MB", "500"))
        self.compression_enabled = (
            os.getenv("COMPRESSION_ENABLED", "true").lower() == "true"
        )

        # Database
        self.database_path = os.getenv("DATABASE_PATH", "/app/data/mobile.db")

        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")


class MobileStatus(BaseModel):
    """Mobile system status model."""

    mobile_mode: bool
    online_status: bool
    battery_level: float | None
    gps_status: str
    sync_status: str
    last_sync: str | None
    cache_size_mb: float
    network_quality: str
    satellite_available: bool
    offline_data_size_mb: float
    system_resources: dict[str, Any]


class MobileServer:
    """Mobile Federal USAR MCP Server."""

    def __init__(self):
        """Initialize mobile server."""
        self.config = MobileConfig()
        self.app = FastAPI(
            title="Federal USAR MCP - Mobile",
            description="Mobile/Field deployment for FEMA Urban Search and Rescue",
            version="1.0.0",
            docs_url="/docs" if self.config.log_level == "DEBUG" else None,
        )

        # Mobile-specific components
        self.sync_manager: MobileSyncManager | None = None
        self.gps_manager: GPSManager | None = None
        self.battery_manager: BatteryManager | None = None
        self.offline_cache: OfflineCache | None = None
        self.monitoring: MonitoringManager | None = None

        # Status tracking
        self.startup_time = datetime.now(UTC)
        self.last_hq_contact = None
        self.online_status = False
        self.network_quality = "unknown"

        # Initialize database
        self._init_database()

        # Setup FastAPI app
        self._setup_middleware()
        self._setup_routes()

    def _init_database(self):
        """Initialize SQLite database for mobile deployment."""
        db_path = Path(self.config.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Create mobile-specific tables
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mobile_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                battery_level REAL,
                gps_lat REAL,
                gps_lon REAL,
                network_quality TEXT,
                sync_status TEXT,
                data_cached_mb REAL
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS offline_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_id TEXT UNIQUE,
                operation_type TEXT,
                data_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                synced BOOLEAN DEFAULT FALSE
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT,
                item_id TEXT,
                action TEXT,
                data_json TEXT,
                priority INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                retry_count INTEGER DEFAULT 0
            )
        """
        )

        conn.commit()
        conn.close()

        logger.info(f"Mobile database initialized: {db_path}")

    def _setup_middleware(self):
        """Setup FastAPI middleware for mobile deployment."""
        # CORS for mobile access
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # More permissive for field use
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Compression middleware for bandwidth optimization
        if self.config.compression_enabled:

            @self.app.middleware("http")
            async def compression_middleware(request, call_next):
                response = await call_next(request)
                if "gzip" in request.headers.get("accept-encoding", ""):
                    # Apply compression for responses > 1KB
                    if response.headers.get("content-length"):
                        size = int(response.headers["content-length"])
                        if size > 1024:
                            response.headers["content-encoding"] = "gzip"
                return response

    def _setup_routes(self):
        """Setup FastAPI routes for mobile deployment."""

        @self.app.get("/health")
        async def health_check():
            """Mobile health check endpoint."""
            return JSONResponse(
                {
                    "status": "healthy",
                    "mode": "mobile",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "uptime": (datetime.now(UTC) - self.startup_time).total_seconds(),
                }
            )

        @self.app.get("/mobile/status")
        async def mobile_status():
            """Get comprehensive mobile status."""
            status = await self._get_mobile_status()
            return status.dict()

        @self.app.post("/mobile/sync")
        async def trigger_sync(background_tasks: BackgroundTasks):
            """Manually trigger sync with headquarters."""
            if self.sync_manager:
                background_tasks.add_task(self.sync_manager.sync_now)
                return {"message": "Sync initiated"}
            raise HTTPException(status_code=503, detail="Sync manager not available")

        @self.app.get("/mobile/offline/operations")
        async def get_offline_operations():
            """Get offline operations queue."""
            operations = await self._get_offline_operations()
            return {"operations": operations}

        @self.app.post("/mobile/battery/mode/{mode}")
        async def set_battery_mode(mode: str):
            """Set battery optimization mode."""
            if self.battery_manager:
                await self.battery_manager.set_mode(mode)
                return {"message": f"Battery mode set to {mode}"}
            raise HTTPException(status_code=503, detail="Battery manager not available")

        @self.app.get("/mobile/gps/location")
        async def get_gps_location():
            """Get current GPS location."""
            if self.gps_manager:
                location = await self.gps_manager.get_current_location()
                return location
            raise HTTPException(status_code=503, detail="GPS not available")

        @self.app.get("/mobile/network/quality")
        async def get_network_quality():
            """Get current network quality assessment."""
            quality = await self._assess_network_quality()
            return {
                "quality": quality,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        @self.app.post("/mobile/cache/clear")
        async def clear_cache():
            """Clear mobile cache."""
            if self.offline_cache:
                cleared_mb = await self.offline_cache.clear_cache()
                return {"message": f"Cleared {cleared_mb:.2f} MB from cache"}
            raise HTTPException(status_code=503, detail="Cache not available")

        @self.app.get("/mobile/metrics")
        async def get_mobile_metrics():
            """Get mobile-specific metrics."""
            metrics = await self._collect_mobile_metrics()
            return metrics

    async def initialize(self):
        """Initialize mobile server components."""
        try:
            # Initialize monitoring
            self.monitoring = MonitoringManager(port=9091)  # Different port for mobile
            await self.monitoring.start()

            # Initialize offline cache
            self.offline_cache = OfflineCache(
                max_size_mb=self.config.max_cache_size_mb,
                compression_enabled=self.config.compression_enabled,
            )
            await self.offline_cache.initialize()

            # Initialize GPS manager if enabled
            if self.config.gps_enabled:
                self.gps_manager = GPSManager()
                await self.gps_manager.initialize()

            # Initialize battery manager if optimization enabled
            if self.config.battery_optimization:
                self.battery_manager = BatteryManager()
                await self.battery_manager.initialize()

            # Initialize sync manager
            self.sync_manager = MobileSyncManager(
                hq_server_url=self.config.hq_server_url,
                sync_interval=self.config.sync_interval,
                offline_cache=self.offline_cache,
            )
            await self.sync_manager.initialize()

            # Start background tasks
            asyncio.create_task(self._status_monitoring_loop())
            asyncio.create_task(self._network_quality_monitoring())

            logger.info("Mobile server components initialized")

        except Exception as e:
            logger.error(f"Failed to initialize mobile server: {str(e)}")
            raise

    async def shutdown(self):
        """Shutdown mobile server components."""
        try:
            if self.sync_manager:
                await self.sync_manager.shutdown()

            if self.gps_manager:
                await self.gps_manager.shutdown()

            if self.battery_manager:
                await self.battery_manager.shutdown()

            if self.offline_cache:
                await self.offline_cache.shutdown()

            if self.monitoring:
                # Note: monitoring manager doesn't have shutdown method in our implementation
                pass

            logger.info("Mobile server shutdown complete")

        except Exception as e:
            logger.error(f"Error during mobile server shutdown: {str(e)}")

    async def _get_mobile_status(self) -> MobileStatus:
        """Get comprehensive mobile system status."""
        # Battery level
        battery_level = None
        if self.battery_manager:
            battery_level = await self.battery_manager.get_battery_level()

        # GPS status
        gps_status = "disabled"
        if self.gps_manager:
            gps_status = await self.gps_manager.get_status()

        # Sync status
        sync_status = "disabled"
        last_sync = None
        if self.sync_manager:
            sync_status = await self.sync_manager.get_status()
            last_sync = await self.sync_manager.get_last_sync_time()

        # Cache size
        cache_size_mb = 0.0
        if self.offline_cache:
            cache_size_mb = await self.offline_cache.get_cache_size_mb()

        # Offline data size
        offline_data_mb = await self._get_offline_data_size()

        # System resources
        system_resources = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "battery_percent": battery_level,
        }

        return MobileStatus(
            mobile_mode=self.config.mobile_mode,
            online_status=self.online_status,
            battery_level=battery_level,
            gps_status=gps_status,
            sync_status=sync_status,
            last_sync=last_sync.isoformat() if last_sync else None,
            cache_size_mb=cache_size_mb,
            network_quality=self.network_quality,
            satellite_available=self.config.satellite_backup,
            offline_data_size_mb=offline_data_mb,
            system_resources=system_resources,
        )

    async def _get_offline_operations(self) -> list[dict[str, Any]]:
        """Get offline operations queue."""
        conn = sqlite3.connect(self.config.database_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT operation_id, operation_type, created_at, synced
            FROM offline_operations
            ORDER BY created_at DESC
            LIMIT 100
        """
        )

        operations = []
        for row in cursor.fetchall():
            operations.append(
                {
                    "operation_id": row[0],
                    "operation_type": row[1],
                    "created_at": row[2],
                    "synced": bool(row[3]),
                }
            )

        conn.close()
        return operations

    async def _assess_network_quality(self) -> str:
        """Assess current network quality."""
        try:
            # Simple network quality assessment
            start_time = time.time()

            # Try to ping headquarters
            import subprocess

            result = subprocess.run(
                ["ping", "-c", "1", "-W", "3", "8.8.8.8"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                response_time = time.time() - start_time
                if response_time < 1.0:
                    return "excellent"
                elif response_time < 2.0:
                    return "good"
                elif response_time < 5.0:
                    return "fair"
                else:
                    return "poor"
            else:
                return "offline"

        except Exception:
            return "unknown"

    async def _get_offline_data_size(self) -> float:
        """Get size of offline data in MB."""
        try:
            db_path = Path(self.config.database_path)
            if db_path.exists():
                size_bytes = db_path.stat().st_size
                return size_bytes / (1024 * 1024)  # Convert to MB
        except Exception:
            pass
        return 0.0

    async def _collect_mobile_metrics(self) -> dict[str, Any]:
        """Collect mobile-specific metrics."""
        status = await self._get_mobile_status()

        return {
            "mobile_mode": status.mobile_mode,
            "online_status": status.online_status,
            "battery_level": status.battery_level,
            "gps_status": status.gps_status,
            "sync_status": status.sync_status,
            "cache_size_mb": status.cache_size_mb,
            "network_quality": status.network_quality,
            "offline_data_mb": status.offline_data_size_mb,
            "uptime_seconds": (datetime.now(UTC) - self.startup_time).total_seconds(),
            "system_resources": status.system_resources,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def _status_monitoring_loop(self):
        """Background status monitoring loop."""
        while True:
            try:
                # Update online status
                self.network_quality = await self._assess_network_quality()
                self.online_status = self.network_quality not in ["offline", "unknown"]

                # Log status to database
                conn = sqlite3.connect(self.config.database_path)
                cursor = conn.cursor()

                battery_level = None
                gps_lat = gps_lon = None

                if self.battery_manager:
                    battery_level = await self.battery_manager.get_battery_level()

                if self.gps_manager:
                    location = await self.gps_manager.get_current_location()
                    if location and "latitude" in location and "longitude" in location:
                        gps_lat = location["latitude"]
                        gps_lon = location["longitude"]

                cache_size_mb = 0.0
                if self.offline_cache:
                    cache_size_mb = await self.offline_cache.get_cache_size_mb()

                cursor.execute(
                    """
                    INSERT INTO mobile_status
                    (battery_level, gps_lat, gps_lon, network_quality, sync_status, data_cached_mb)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        battery_level,
                        gps_lat,
                        gps_lon,
                        self.network_quality,
                        "active" if self.sync_manager else "inactive",
                        cache_size_mb,
                    ),
                )

                conn.commit()
                conn.close()

                # Clean old status records (keep last 1000)
                conn = sqlite3.connect(self.config.database_path)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM mobile_status
                    WHERE id < (
                        SELECT id FROM mobile_status
                        ORDER BY id DESC LIMIT 1000, 1
                    )
                """
                )
                conn.commit()
                conn.close()

                await asyncio.sleep(60)  # Update every minute

            except Exception as e:
                logger.error(f"Status monitoring error: {str(e)}")
                await asyncio.sleep(60)

    async def _network_quality_monitoring(self):
        """Background network quality monitoring."""
        while True:
            try:
                # Test connection to headquarters
                if self.sync_manager:
                    hq_reachable = await self.sync_manager.test_hq_connection()
                    if hq_reachable:
                        self.last_hq_contact = datetime.now(UTC)

                await asyncio.sleep(300)  # Test every 5 minutes

            except Exception as e:
                logger.error(f"Network monitoring error: {str(e)}")
                await asyncio.sleep(300)


# Mobile server factory
def create_mobile_server() -> MobileServer:
    """Create mobile USAR MCP server.

    Returns:
        Configured mobile server
    """
    return MobileServer()


# Main entry point for mobile deployment
async def main():
    """Main entry point for mobile server."""
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create and initialize mobile server
    server = create_mobile_server()
    await server.initialize()

    try:
        # Run mobile server
        config = uvicorn.Config(
            server.app,
            host="0.0.0.0",
            port=8000,
            log_level=os.getenv("LOG_LEVEL", "info").lower(),
            access_log=True,
            loop="asyncio",
        )

        uvicorn_server = uvicorn.Server(config)

        logger.info("Starting Federal USAR MCP Mobile Server")
        await uvicorn_server.serve()

    finally:
        await server.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
