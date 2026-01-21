"""Planned workouts API schemas - simplified, no plan grouping."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class PlannedWorkoutResponse(BaseModel):
    """Planned workout response."""

    id: int
    planned_date: date
    activity_type: str
    workout_type: Optional[str] = None
    title: str
    description: Optional[str] = None
    structured_workout: Optional[str] = None
    target_duration_s: Optional[float] = None
    target_distance_m: Optional[float] = None
    target_tss: Optional[float] = None
    target_hr_zone: Optional[int] = None
    target_pace_minkm: Optional[float] = None
    status: str
    completed_activity_id: Optional[int] = None
    created_at: Optional[datetime] = None


class GenerateWorkoutsRequest(BaseModel):
    """Request to generate workouts."""

    prompt: str


class GeneratedWorkoutsResponse(BaseModel):
    """Response containing generated and saved workouts."""

    workouts: list[PlannedWorkoutResponse]
    count: int


class UpcomingWorkoutsResponse(BaseModel):
    """Response containing upcoming workouts."""

    workouts: list[PlannedWorkoutResponse]
    days: int


class DateWorkoutsResponse(BaseModel):
    """Response containing workouts for a specific date."""

    date: date
    workouts: list[PlannedWorkoutResponse]
