"""Coaching API schemas for unified chat with tool-calling."""

from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel


class ConversationMessage(BaseModel):
    """A message in the coaching conversation."""

    role: Literal["user", "assistant"]
    content: str


class CoachingChatRequest(BaseModel):
    """Request to chat with the coaching assistant."""

    message: str
    conversation_history: list[ConversationMessage] = []


class WorkoutProposal(BaseModel):
    """A proposed workout from the coaching assistant."""

    date: str  # ISO format YYYY-MM-DD
    activity_type: str
    workout_type: Optional[str] = None
    title: str
    description: Optional[str] = None
    target_duration_minutes: int
    target_tss: Optional[int] = None
    target_calories: Optional[int] = None
    existing_workout_id: Optional[int] = None  # Set if modifying existing


class WorkoutDeletion(BaseModel):
    """A proposed workout deletion."""

    workout_id: int
    title: str
    date: str


class AcceptCoachingProposalRequest(BaseModel):
    """Request to accept a coaching proposal."""

    proposal_id: str
    workouts: list[WorkoutProposal] = []
    deletions: list[WorkoutDeletion] = []


class AcceptCoachingProposalResponse(BaseModel):
    """Response after accepting a coaching proposal."""

    created_ids: list[int]
    updated_ids: list[int]
    deleted_ids: list[int]
    message: str
