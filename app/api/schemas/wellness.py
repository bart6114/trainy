"""Wellness API schemas for settings, morning check-ins, and feedback."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserSettingsResponse(BaseModel):
    """User wellness settings response."""

    id: Optional[int] = None

    # Morning check-in toggles
    morning_checkin_enabled: bool = False
    morning_sleep_quality_enabled: bool = False
    morning_sleep_hours_enabled: bool = False
    morning_muscle_soreness_enabled: bool = False
    morning_energy_enabled: bool = False
    morning_mood_enabled: bool = False

    # Post-workout feedback toggles
    post_workout_feedback_enabled: bool = False
    post_workout_rpe_enabled: bool = False
    post_workout_pain_enabled: bool = False
    post_workout_session_feel_enabled: bool = False
    post_workout_notes_enabled: bool = False


class UserSettingsUpdateRequest(BaseModel):
    """User settings update request."""

    morning_checkin_enabled: Optional[bool] = None
    morning_sleep_quality_enabled: Optional[bool] = None
    morning_sleep_hours_enabled: Optional[bool] = None
    morning_muscle_soreness_enabled: Optional[bool] = None
    morning_energy_enabled: Optional[bool] = None
    morning_mood_enabled: Optional[bool] = None

    post_workout_feedback_enabled: Optional[bool] = None
    post_workout_rpe_enabled: Optional[bool] = None
    post_workout_pain_enabled: Optional[bool] = None
    post_workout_session_feel_enabled: Optional[bool] = None
    post_workout_notes_enabled: Optional[bool] = None


class MorningCheckinResponse(BaseModel):
    """Morning check-in response."""

    id: Optional[int] = None
    checkin_date: date

    sleep_quality: Optional[int] = None
    sleep_hours: Optional[float] = None
    muscle_soreness: Optional[int] = None
    energy_level: Optional[int] = None
    mood: Optional[int] = None

    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class MorningCheckinRequest(BaseModel):
    """Morning check-in create/update request."""

    checkin_date: date

    sleep_quality: Optional[int] = Field(None, ge=1, le=10)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    muscle_soreness: Optional[int] = Field(None, ge=1, le=10)
    energy_level: Optional[int] = Field(None, ge=1, le=10)
    mood: Optional[int] = Field(None, ge=1, le=10)

    notes: Optional[str] = None


class PendingActivityItem(BaseModel):
    """Activity pending feedback."""

    id: int
    activity_type: str
    title: Optional[str]
    start_time: datetime
    duration_seconds: float
    distance_meters: Optional[float]


class PendingFeedbackResponse(BaseModel):
    """Response with pending feedback items."""

    activities: list[PendingActivityItem]
    morning_checkin_pending: bool
    total_count: int


class ActivityFeedbackResponse(BaseModel):
    """Activity feedback response."""

    id: Optional[int] = None
    activity_id: int

    rpe: Optional[int] = None
    comfort_level: Optional[int] = None  # "session feel"
    has_pain: bool = False
    pain_location: Optional[str] = None
    pain_severity: Optional[int] = None
    notes: Optional[str] = None

    created_at: Optional[datetime] = None


class ActivityFeedbackRequest(BaseModel):
    """Activity feedback create/update request."""

    rpe: Optional[int] = Field(None, ge=1, le=10)
    comfort_level: Optional[int] = Field(None, ge=1, le=10)  # "session feel"
    has_pain: bool = False
    pain_location: Optional[str] = None
    pain_severity: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None
