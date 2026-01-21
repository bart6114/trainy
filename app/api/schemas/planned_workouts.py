"""Planned workouts API schemas - simplified, no plan grouping."""

from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel


# Conversation types for chat-based planning
class ConversationMessage(BaseModel):
    """A message in the planning conversation."""

    role: Literal["user", "assistant"]
    content: str


class WorkoutProposalItem(BaseModel):
    """A single workout in a proposal (before saving to DB)."""

    date: date
    activity_type: str
    workout_type: Optional[str] = None
    title: str
    description: Optional[str] = None
    target_duration_minutes: int
    target_tss: Optional[int] = None


class GenerateStreamRequest(BaseModel):
    """Request to generate workouts with streaming."""

    prompt: str
    conversation_history: list[ConversationMessage] = []


class RefineStreamRequest(BaseModel):
    """Request to refine a workout proposal."""

    refinement: str
    current_proposal: list[WorkoutProposalItem]
    conversation_history: list[ConversationMessage]


class AcceptProposalRequest(BaseModel):
    """Request to accept and save a workout proposal."""

    workouts: list[WorkoutProposalItem]


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


class ClarifyingQuestion(BaseModel):
    """A question the AI wants to ask before generating."""

    message: str
    options: list[str] | None = None  # Optional predefined choices
