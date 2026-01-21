"""Profile API schemas."""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class ProfileResponse(BaseModel):
    """User profile response."""

    id: Optional[int] = None
    ftp: int
    lthr: int
    max_hr: int
    resting_hr: int
    threshold_pace_minkm: float
    swim_threshold_pace: float
    weight_kg: float
    effective_from: date
    metrics_dirty: bool


class ProfileUpdateRequest(BaseModel):
    """Profile update request."""

    ftp: Optional[int] = Field(None, ge=50, le=500)
    lthr: Optional[int] = Field(None, ge=100, le=220)
    max_hr: Optional[int] = Field(None, ge=120, le=250)
    resting_hr: Optional[int] = Field(None, ge=30, le=100)
    threshold_pace_minkm: Optional[float] = Field(None, ge=2.0, le=15.0)
    swim_threshold_pace: Optional[float] = Field(None, ge=0.5, le=5.0)
    weight_kg: Optional[float] = Field(None, ge=30.0, le=200.0)


class MaxHRDetectionResponse(BaseModel):
    """Response from max HR auto-detection."""

    detected_max_hr: Optional[int] = None
    sample_count: int
    confidence: str  # 'high', 'medium', 'low', 'none'
    message: str
