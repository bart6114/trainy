"""Activity API schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, computed_field

from .common import PaginatedResponse


class ActivityResponse(BaseModel):
    """Activity response without raw FIT data."""

    id: int
    fit_file_hash: str
    start_time: datetime
    end_time: Optional[datetime] = None
    activity_type: str
    source: Optional[str] = None
    duration_seconds: float
    distance_meters: Optional[float] = None
    avg_speed_mps: Optional[float] = None
    max_speed_mps: Optional[float] = None
    total_ascent_m: Optional[float] = None
    total_descent_m: Optional[float] = None
    avg_hr: Optional[int] = None
    max_hr: Optional[int] = None
    avg_power: Optional[float] = None
    max_power: Optional[float] = None
    normalized_power: Optional[float] = None
    avg_cadence: Optional[int] = None
    calories: Optional[int] = None
    title: Optional[str] = None
    imported_at: Optional[datetime] = None

    @computed_field
    @property
    def duration_formatted(self) -> str:
        """Format duration in human readable format."""
        hours = int(self.duration_seconds // 3600)
        minutes = int((self.duration_seconds % 3600) // 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    @computed_field
    @property
    def distance_km(self) -> Optional[float]:
        """Distance in kilometers."""
        if self.distance_meters:
            return round(self.distance_meters / 1000, 2)
        return None


class ActivityMetricsResponse(BaseModel):
    """Activity metrics response."""

    activity_id: int
    tss: Optional[float] = None
    tss_method: Optional[str] = None
    intensity_factor: Optional[float] = None
    efficiency_factor: Optional[float] = None  # Power/speed per HR beat
    variability_index: Optional[float] = None  # NP/AP ratio (cycling)
    peak_power_5s: Optional[float] = None
    peak_power_1min: Optional[float] = None
    peak_power_5min: Optional[float] = None
    peak_power_20min: Optional[float] = None
    calculated_at: Optional[datetime] = None


class ActivityWithMetricsResponse(BaseModel):
    """Activity with its computed metrics."""

    activity: ActivityResponse
    metrics: Optional[ActivityMetricsResponse] = None


class ActivityListResponse(PaginatedResponse[ActivityResponse]):
    """Paginated list of activities."""

    pass
