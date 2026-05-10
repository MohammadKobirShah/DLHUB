"""
DLHUB - Metrics Service
========================
Prometheus-style metrics collection.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

from app.config import settings

logger = logging.getLogger(__name__)


class Metrics:
    """Simple metrics collector."""

    def __init__(self):
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, list] = defaultdict(list)
        self.start_time = time.time()

    def increment(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a counter."""
        key = self._make_key(name, labels)
        self.counters[key] += value

    def gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge value."""
        key = self._make_key(name, labels)
        self.gauges[key] = value

    def histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Add to histogram."""
        key = self._make_key(name, labels)
        self.histograms[key].append(value)

    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create metric key with labels."""
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format."""
        lines = []

        lines.append("# HELP dlhub_build_info DLHUB build information")
        lines.append(f"# TYPE dlhub_build_info gauge")
        lines.append(f'dlhub_build_info{{version="{settings.VERSION}"}} 1')

        uptime = time.time() - self.start_time
        lines.append("# HELP dlhub_uptime_seconds DLHUB uptime in seconds")
        lines.append("# TYPE dlhub_uptime_seconds gauge")
        lines.append(f"dlhub_uptime_seconds {uptime}")

        lines.append("# HELP dlhub_downloads_total Total number of downloads")
        lines.append("# TYPE dlhub_downloads_total counter")
        total_downloads = self.counters.get("downloads_total", 0)
        lines.append(f"dlhub_downloads_total {total_downloads}")

        lines.append("# HELP dlhub_downloads_active Active downloads")
        lines.append("# TYPE dlhub_downloads_active gauge")
        lines.append(f"dlhub_downloads_active {self.gauges.get('downloads_active', 0)}")

        lines.append("# HELP dlhub_downloads_failed Total failed downloads")
        lines.append("# TYPE dlhub_downloads_failed counter")
        lines.append(f"dlhub_downloads_failed {self.counters.get('downloads_failed', 0)}")

        lines.append("# HELP dlhub_queue_size Current queue size")
        lines.append("# TYPE dlhub_queue_size gauge")
        lines.append(f"dlhub_queue_size {self.gauges.get('queue_size', 0)}")

        lines.append("# HELP dlhub_processing_time_seconds Download processing time")
        lines.append("# TYPE dlhub_processing_time_seconds histogram")
        times = self.histograms.get("processing_time", [])
        if times:
            avg_time = sum(times) / len(times)
            lines.append(f"dlhub_processing_time_seconds_sum {avg_time * len(times)}")
            lines.append(f"dlhub_processing_time_seconds_count {len(times)}")

        lines.append("# HELP dlhub_storage_used_bytes Storage used in bytes")
        lines.append("# TYPE dlhub_storage_used_bytes gauge")
        lines.append(f"dlhub_storage_used_bytes {self.gauges.get('storage_used_bytes', 0)}")

        lines.append("# HELP dlhub_bandwidth_bytes_total Total bandwidth used")
        lines.append("# TYPE dlhub_bandwidth_bytes_total counter")
        lines.append(f"dlhub_bandwidth_bytes_total {self.counters.get('bandwidth_bytes_total', 0)}")

        lines.append("# HELP dlhub_requests_total Total API requests")
        lines.append("# TYPE dlhub_requests_total counter")
        lines.append(f"dlhub_requests_total {self.counters.get('requests_total', 0)}")

        lines.append("# HELP dlhub_request_duration_seconds API request duration")
        lines.append("# TYPE dlhub_request_duration_seconds histogram")

        return "\n".join(lines)

    def reset(self):
        """Reset all metrics."""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()


metrics = Metrics()


class MetricsMiddleware:
    """Middleware to track request metrics."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        await self.app(scope, receive, send)

        duration = time.time() - start_time
        path = scope.get("path", "/")

        metrics.increment("requests_total")
        metrics.histogram("request_duration", duration, {"path": path})


async def track_download_start():
    """Track download start."""
    metrics.increment("downloads_total")
    metrics.gauge("downloads_active", metrics.gauges.get("downloads_active", 0) + 1)


async def track_download_complete(duration: float, size: int):
    """Track download completion."""
    active = metrics.gauges.get("downloads_active", 1)
    metrics.gauge("downloads_active", max(0, active - 1))
    metrics.histogram("processing_time", duration)
    metrics.increment("bandwidth_bytes_total", size)


async def track_download_failed():
    """Track download failure."""
    metrics.increment("downloads_failed")


async def update_queue_size(size: int):
    """Update queue size gauge."""
    metrics.gauge("queue_size", size)


async def update_storage_used(bytes_used: int):
    """Update storage used gauge."""
    metrics.gauge("storage_used_bytes", bytes_used)