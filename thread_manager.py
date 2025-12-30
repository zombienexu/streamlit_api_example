"""
Thread manager for orchestrating parallel API calls with status tracking.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from api_simulator import (
    APIResult,
    GeoBox,
    SimulatedAPI,
    TimeRange,
    simulate_api_call,
)


class APIStatus(Enum):
    """Status of an API task."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class APITask:
    """Tracks the state of a single API task."""
    api: SimulatedAPI
    status: APIStatus = APIStatus.PENDING
    start_time: float | None = None
    end_time: float | None = None
    result: APIResult | None = None

    @property
    def elapsed_time(self) -> float | None:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return None
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

    @property
    def elapsed_time_str(self) -> str:
        """Get formatted elapsed time string."""
        elapsed = self.elapsed_time
        if elapsed is None:
            return "..."
        return f"{elapsed:.1f}s"


@dataclass
class ThreadManager:
    """Manages parallel API calls with thread-safe status tracking."""

    tasks: dict[str, APITask] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _executor: ThreadPoolExecutor | None = None

    def submit_all(
        self,
        apis: list[SimulatedAPI],
        query_name: str,
        time_range: TimeRange,
        geo_box: GeoBox,
    ) -> None:
        """
        Submit all API calls to the thread pool.

        Args:
            apis: List of APIs to call
            query_name: Name of the query
            time_range: Time range for the query
            geo_box: Geographic bounding box
        """
        # Initialize tasks
        with self._lock:
            self.tasks = {api.name: APITask(api=api) for api in apis}

        # Create executor and submit all tasks
        self._executor = ThreadPoolExecutor(max_workers=len(apis))

        for api in apis:
            self._executor.submit(
                self._run_task,
                api,
                query_name,
                time_range,
                geo_box,
            )

    def _run_task(
        self,
        api: SimulatedAPI,
        query_name: str,
        time_range: TimeRange,
        geo_box: GeoBox,
    ) -> None:
        """Run a single API task and update its status."""
        # Mark as running
        with self._lock:
            task = self.tasks[api.name]
            task.status = APIStatus.RUNNING
            task.start_time = time.time()

        try:
            # Execute the API call
            result = simulate_api_call(api, query_name, time_range, geo_box)

            # Update status based on result
            with self._lock:
                task = self.tasks[api.name]
                task.end_time = time.time()
                task.result = result
                task.status = APIStatus.SUCCESS if result.success else APIStatus.ERROR

        except Exception as e:
            # Handle unexpected errors
            with self._lock:
                task = self.tasks[api.name]
                task.end_time = time.time()
                task.result = APIResult(success=False, error=str(e))
                task.status = APIStatus.ERROR

    def get_tasks(self) -> dict[str, APITask]:
        """Get a snapshot of all tasks."""
        with self._lock:
            return dict(self.tasks)

    def is_complete(self) -> bool:
        """Check if all tasks are complete."""
        with self._lock:
            if not self.tasks:
                return False
            return all(
                task.status in (APIStatus.SUCCESS, APIStatus.ERROR)
                for task in self.tasks.values()
            )

    def shutdown(self) -> None:
        """Shutdown the thread pool executor."""
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
