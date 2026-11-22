from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.services.automation_service import sync_gmail_transactions
from app.services.database_service import DatabaseService

logger = logging.getLogger("bijlitrack.scheduler")


class BackgroundSyncManager:
    """Async background worker for automatic periodic Gmail synchronization."""

    def __init__(self) -> None:
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._is_syncing: bool = False
        self._last_error: Optional[str] = None
        self._last_sync_time: Optional[str] = None
        self._last_saved_count: int = 0
        self._sync_status: str = "idle"

    async def start(self) -> None:
        """Start background scheduler loop."""
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Background sync scheduler started.")

    async def stop(self) -> None:
        """Gracefully stop background scheduler."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            logger.info("Background sync scheduler stopped.")

    async def run_sync_job(self) -> Dict[str, Any]:
        """Execute a sync job protected by lock."""
        if self._lock.locked():
            return {
                "status": "already_running",
                "message": "Synchronization is already in progress.",
            }

        async with self._lock:
            self._is_syncing = True
            self._sync_status = "syncing"
            try:
                # Run sync in threadpool so it doesn't block the async event loop
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, sync_gmail_transactions)
                self._last_sync_time = datetime.utcnow().isoformat()
                self._last_saved_count = result.get("saved_transactions", 0)
                self._sync_status = "success"
                self._last_error = None
                return result
            except Exception as exc:
                err_msg = str(exc)
                logger.error("Background Gmail sync error: %s", err_msg)
                self._sync_status = "error"
                self._last_error = err_msg
                return {
                    "status": "error",
                    "message": err_msg,
                    "saved_transactions": 0,
                    "transactions": [],
                }
            finally:
                self._is_syncing = False

    async def _scheduler_loop(self) -> None:
        """Periodic background execution."""
        # Initial wait of 20 seconds after server boot before first check
        await asyncio.sleep(20)

        while True:
            try:
                db = DatabaseService()
                auto_enabled = db.get_setting("auto_sync_enabled", "true").lower() == "true"
                interval_minutes = int(db.get_setting("sync_interval_minutes", "30"))
                interval_seconds = max(interval_minutes * 60, 300)  # Minimum 5 minutes

                if auto_enabled:
                    logger.info("Running automatic scheduled Gmail sync...")
                    await self.run_sync_job()

                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Error in scheduler loop: %s", exc)
                await asyncio.sleep(60)

    def get_status(self) -> Dict[str, Any]:
        db = DatabaseService()
        settings = db.get_all_settings()
        last_time = self._last_sync_time or settings.get("last_sync_time")
        status_text = self._sync_status if self._is_syncing else settings.get("last_sync_status", "Idle")

        return {
            "is_syncing": self._is_syncing,
            "status": status_text,
            "last_sync_time": last_time,
            "last_saved_count": self._last_saved_count,
            "last_error": self._last_error,
            "auto_sync_enabled": settings.get("auto_sync_enabled", "true").lower() == "true",
            "interval_minutes": int(settings.get("sync_interval_minutes", "30")),
        }


# Global singleton instance
sync_manager = BackgroundSyncManager()
