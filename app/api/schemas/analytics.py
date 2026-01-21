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
