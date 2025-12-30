"""
Simulated API module for testing multi-threaded API calls.
Each API has configurable duration and failure rate.
"""

import random
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class SimulatedAPI:
    """Configuration for a simulated API."""
    name: str
    min_duration: float  # seconds
    max_duration: float  # seconds
    failure_rate: float  # 0.0 to 1.0


# Define 5 simulated APIs with different characteristics
SIMULATED_APIS = [
    SimulatedAPI(
        name="Weather API",
        min_duration=1.0,
        max_duration=2.0,
        failure_rate=0.05,
    ),
    SimulatedAPI(
        name="Satellite Data API",
        min_duration=3.0,
        max_duration=5.0,
        failure_rate=0.15,
    ),
    SimulatedAPI(
        name="Population API",
        min_duration=2.0,
        max_duration=3.0,
        failure_rate=0.05,
    ),
    SimulatedAPI(
        name="Traffic API",
        min_duration=1.0,
        max_duration=2.0,
        failure_rate=0.20,
    ),
    SimulatedAPI(
        name="Air Quality API",
        min_duration=2.0,
        max_duration=4.0,
        failure_rate=0.08,
    ),
]


@dataclass
class GeoBox:
    """Geographic bounding box defined by corners."""
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


@dataclass
class TimeRange:
    """Time range for the query."""
    start: datetime
    end: datetime


@dataclass
class APIResult:
    """Result from a simulated API call."""
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


def simulate_api_call(
    api: SimulatedAPI,
    query_name: str,
    time_range: TimeRange,
    geo_box: GeoBox,
) -> APIResult:
    """
    Simulate an API call with random duration and possible failure.

    Args:
        api: The simulated API configuration
        query_name: Name of the query
        time_range: Time range for the query
        geo_box: Geographic bounding box

    Returns:
        APIResult with success/failure and data or error message
    """
    # Random duration within the API's range
    duration = random.uniform(api.min_duration, api.max_duration)
    time.sleep(duration)

    # Random failure based on failure rate
    if random.random() < api.failure_rate:
        error_messages = [
            "Connection timeout",
            "Rate limit exceeded",
            "Service temporarily unavailable",
            "Invalid response from server",
            "Authentication failed",
        ]
        return APIResult(
            success=False,
            error=random.choice(error_messages),
        )

    # Generate mock data based on API type
    data = _generate_mock_data(api.name, query_name, time_range, geo_box)

    return APIResult(success=True, data=data)


def _generate_mock_data(
    api_name: str,
    query_name: str,
    time_range: TimeRange,
    geo_box: GeoBox,
) -> dict[str, Any]:
    """Generate mock data based on the API type."""

    base_data = {
        "query_name": query_name,
        "time_range": {
            "start": time_range.start.isoformat(),
            "end": time_range.end.isoformat(),
        },
        "geo_box": {
            "min_lat": geo_box.min_lat,
            "min_lon": geo_box.min_lon,
            "max_lat": geo_box.max_lat,
            "max_lon": geo_box.max_lon,
        },
    }

    if api_name == "Weather API":
        base_data["weather"] = {
            "temperature_avg": round(random.uniform(10, 35), 1),
            "humidity_avg": round(random.uniform(30, 90), 1),
            "precipitation_mm": round(random.uniform(0, 50), 1),
            "wind_speed_kmh": round(random.uniform(0, 30), 1),
        }
    elif api_name == "Satellite Data API":
        base_data["satellite"] = {
            "cloud_cover_pct": round(random.uniform(0, 100), 1),
            "ndvi_avg": round(random.uniform(-0.2, 0.8), 3),
            "images_available": random.randint(5, 50),
            "resolution_m": random.choice([10, 30, 60]),
        }
    elif api_name == "Population API":
        base_data["population"] = {
            "total_population": random.randint(10000, 5000000),
            "density_per_km2": round(random.uniform(10, 10000), 1),
            "urban_pct": round(random.uniform(20, 95), 1),
        }
    elif api_name == "Traffic API":
        base_data["traffic"] = {
            "congestion_index": round(random.uniform(0, 10), 2),
            "avg_speed_kmh": round(random.uniform(15, 80), 1),
            "incidents_count": random.randint(0, 20),
        }
    elif api_name == "Air Quality API":
        base_data["air_quality"] = {
            "aqi": random.randint(20, 200),
            "pm25_ugm3": round(random.uniform(5, 100), 1),
            "pm10_ugm3": round(random.uniform(10, 150), 1),
            "o3_ppb": round(random.uniform(10, 80), 1),
        }

    return base_data
