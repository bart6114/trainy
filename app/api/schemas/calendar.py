"""Calendar API schemas."""

from datetime import date
from typing import Optional
from pydantic import BaseModel


class CalendarActivity(BaseModel):
    """Activity summary for calendar display."""

    id: int
    activity_type: str
    title: Optional[str] = None
    duration_seconds: float
    distance_meters: Optional[float] = None
    tss: Optional[float] = None
    calories: Optional[int] = None


class CalendarPlannedWorkout(BaseModel):
    """Planned workout summary for calendar display."""

    id: int
    activity_type: str
    workout_type: Optional[str] = None
    title: str
    description: Optional[str] = None
    target_duration_s: Optional[float] = None
    target_tss: Optional[float] = None
    target_calories: Optional[int] = None
    status: str
    completed_activity_id: Optional[int] = None


class CalendarDay(BaseModel):
    """Single day in calendar with activities and planned workouts."""

    date: date
    activities: list[CalendarActivity]
    planned_workouts: list[CalendarPlannedWorkout] = []
    total_tss: float
    activity_count: int


class CalendarMonthResponse(BaseModel):
    """Calendar month data."""

    year: int
    month: int
    days: list[CalendarDay]


class CalendarDateResponse(BaseModel):
    """Activities and planned workouts for a specific date."""

    date: date
    activities: list[CalendarActivity]
    planned_workouts: list[CalendarPlannedWorkout] = []
    total_tss: float
