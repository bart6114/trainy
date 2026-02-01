"""Analytics API schemas."""

from datetime import date
from typing import Optional

from pydantic import BaseModel


class PowerCurvePoint(BaseModel):
    """A single point on the power curve."""

    duration_seconds: int
    duration_label: str
    best_watts: Optional[float] = None
    best_watts_per_kg: Optional[float] = None
    activity_id: Optional[int] = None
    activity_date: Optional[date] = None


class PowerCurveResponse(BaseModel):
    """Response containing power curve data."""

    start_date: date
    end_date: date
    weight_kg: float
    ftp: int
    eftp: Optional[int] = None
    w_prime: Optional[int] = None  # Anaerobic work capacity (J)
    eftp_method: str = "none"  # "morton_3p" or "20min_95pct"
    points: list[PowerCurvePoint]


# --- Injury Analysis Schemas ---


class PainEvent(BaseModel):
    """A single pain event recorded during workout feedback."""

    date: date
    pain_location: Optional[str] = None
    pain_severity: Optional[int] = None
    activity_type: str
    activity_id: int
    activity_title: Optional[str] = None


class PainLocationSummary(BaseModel):
    """Pain summary aggregated by location."""

    location: Optional[str] = None
    count: int
    avg_severity: Optional[float] = None
    max_severity: Optional[int] = None


class PainActivitySummary(BaseModel):
    """Pain summary aggregated by activity type."""

    activity_type: str
    count: int
    avg_severity: Optional[float] = None


class InjuryAnalysisResponse(BaseModel):
    """Response containing injury analysis data."""

    start_date: date
    end_date: date
    total_pain_events: int
    pain_events: list[PainEvent]
    by_location: list[PainLocationSummary]
    by_activity: list[PainActivitySummary]


# --- Pain Location Merge Schemas ---


class PainLocationCount(BaseModel):
    """A unique pain location with its occurrence count."""

    location: str
    count: int


class MergePainLocationsRequest(BaseModel):
    """Request to merge multiple pain locations into one."""

    source_locations: list[str]
    target_location: str


class MergePainLocationsResponse(BaseModel):
    """Response from merging pain locations."""

    updated_count: int


# --- Rowing PRs Schemas ---


class RowingDistancePR(BaseModel):
    """A personal record for a specific rowing distance."""

    distance_meters: int
    distance_label: str  # "500m", "1k", "2k", "5k", "10k"
    total_seconds: Optional[float] = None
    split_seconds: Optional[float] = None  # Time per 500m
    activity_id: Optional[int] = None
    activity_date: Optional[date] = None


class RowingPowerPR(BaseModel):
    """A personal record for a specific rowing power duration."""

    duration_seconds: int
    duration_label: str  # "1min", "4min", "30min", "60min"
    best_watts: Optional[float] = None
    activity_id: Optional[int] = None
    activity_date: Optional[date] = None


class RowingTimePR(BaseModel):
    """A personal record for best distance covered in a specific time."""

    duration_seconds: int
    duration_label: str  # "1min", "4min", "20min", etc.
    best_distance_meters: Optional[float] = None
    split_seconds: Optional[float] = None  # Pace per 500m
    activity_id: Optional[int] = None
    activity_date: Optional[date] = None


class RowingPRsResponse(BaseModel):
    """Response containing rowing personal records."""

    distance_prs: list[RowingDistancePR]
    time_prs: list[RowingTimePR]
    power_prs: list[RowingPowerPR]
