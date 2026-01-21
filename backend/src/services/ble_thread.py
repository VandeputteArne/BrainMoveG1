"""
BLE Thread Manager - Runs all Bluetooth operations on a separate thread.

This prevents BLE operations from blocking the main asyncio event loop
where Socket.io runs, ensuring socket messages are sent immediately.
"""

import asyncio
import threading
import logging
from concurrent.futures import Future
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


class BLEThread:
    """
    Manages a separate thread with its own event loop for BLE operations.

    Usage:
        ble_thread = BLEThread()
        ble_thread.start()

        # Run async BLE operation from main thread
        result = await ble_thread.run(some_ble_coroutine())

        # Or fire-and-forget (non-blocking)
        ble_thread.run_nowait(some_ble_coroutine())

        ble_thread.stop()
    """

    def __init__(self):
        self._thread: threading.Thread = None
        self._loop: asyncio.AbstractEventLoop = None
        self._started = threading.Event()
        self._stop_event = threading.Event()

    def start(self):
        """Start the BLE thread with its own event loop."""
        if self._thread and self._thread.is_alive():
            logger.warning("BLE thread already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="BLEThread")
        self._thread.start()

        # Wait for the loop to be ready
        self._started.wait(timeout=5.0)
        logger.info("BLE thread started")

    def _run_loop(self):
        """Thread target - creates and runs the event loop."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        self._started.set()

        try:
            self._loop.run_forever()
        finally:
            # Clean up pending tasks
            pending = asyncio.all_tasks(self._loop)
            for task in pending:
                task.cancel()

            # Run until all tasks are cancelled
            if pending:
                self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

            self._loop.close()
            logger.info("BLE thread event loop closed")

    def stop(self):
        """Stop the BLE thread."""
        if not self._loop or not self._thread:
            return

        self._stop_event.set()
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5.0)

        if self._thread.is_alive():
            logger.warning("BLE thread did not stop gracefully")
        else:
            logger.info("BLE thread stopped")

        self._thread = None
        self._loop = None
        self._started.clear()

    def run_nowait(self, coro: Coroutine) -> asyncio.Future:
        """
        Schedule a coroutine on the BLE thread without waiting.
        Returns a Future that can be awaited later if needed.
        """
        if not self._loop:
            raise RuntimeError("BLE thread not started")

        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    async def run(self, coro: Coroutine, timeout: float = 30.0) -> Any:
        """
        Run a coroutine on the BLE thread and wait for the result.
        This is safe to call from the main asyncio thread.
        """
        if not self._loop:
            raise RuntimeError("BLE thread not started")

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)

        # Wait for the result in a non-blocking way
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, future.result, timeout)

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()


# Global BLE thread instance
_ble_thread: BLEThread = None


def get_ble_thread() -> BLEThread:
    """Get or create the global BLE thread."""
    global _ble_thread
    if _ble_thread is None:
        _ble_thread = BLEThread()
    return _ble_thread


def start_ble_thread():
    """Start the global BLE thread."""
    thread = get_ble_thread()
    if not thread.is_running:
        thread.start()
    return thread


def stop_ble_thread():
    """Stop the global BLE thread."""
    global _ble_thread
    if _ble_thread:
        _ble_thread.stop()
        _ble_thread = None
