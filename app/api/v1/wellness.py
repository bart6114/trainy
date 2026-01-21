"""Wellness API endpoints for settings, morning check-ins, and post-workout feedback."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from trainy.database import Repository
from trainy.database.models import UserSettings, MorningCheckin, WorkoutFeedback
from app.dependencies import get_repo
from app.api.schemas.wellness import (
    UserSettingsResponse,
    UserSettingsUpdateRequest,
    MorningCheckinResponse,
    MorningCheckinRequest,
    PendingFeedbackResponse,
    PendingActivityItem,
    ActivityFeedbackResponse,
    ActivityFeedbackRequest,
)

router = APIRouter()


# --- User Settings ---


@router.get("/settings", response_model=UserSettingsResponse)
async def get_settings(repo: Repository = Depends(get_repo)):
    """Get user wellness settings."""
    settings = repo.get_user_settings()
    return UserSettingsResponse(
        id=settings.id,
        morning_checkin_enabled=settings.morning_checkin_enabled,
        morning_sleep_quality_enabled=settings.morning_sleep_quality_enabled,
        morning_sleep_hours_enabled=settings.morning_sleep_hours_enabled,
        morning_muscle_soreness_enabled=settings.morning_muscle_soreness_enabled,
        morning_energy_enabled=settings.morning_energy_enabled,
        morning_mood_enabled=settings.morning_mood_enabled,
        post_workout_feedback_enabled=settings.post_workout_feedback_enabled,
        post_workout_rpe_enabled=settings.post_workout_rpe_enabled,
        post_workout_pain_enabled=settings.post_workout_pain_enabled,
        post_workout_session_feel_enabled=settings.post_workout_session_feel_enabled,
        post_workout_notes_enabled=settings.post_workout_notes_enabled,
    )


@router.put("/settings", response_model=UserSettingsResponse)
async def update_settings(
    request: UserSettingsUpdateRequest,
    repo: Repository = Depends(get_repo),
):
    """Update user wellness settings."""
    current = repo.get_user_settings()

    # Update only provided fields
    if request.morning_checkin_enabled is not None:
        current.morning_checkin_enabled = request.morning_checkin_enabled
    if request.morning_sleep_quality_enabled is not None:
        current.morning_sleep_quality_enabled = request.morning_sleep_quality_enabled
    if request.morning_sleep_hours_enabled is not None:
        current.morning_sleep_hours_enabled = request.morning_sleep_hours_enabled
    if request.morning_muscle_soreness_enabled is not None:
        current.morning_muscle_soreness_enabled = request.morning_muscle_soreness_enabled
    if request.morning_energy_enabled is not None:
        current.morning_energy_enabled = request.morning_energy_enabled
    if request.morning_mood_enabled is not None:
        current.morning_mood_enabled = request.morning_mood_enabled

    if request.post_workout_feedback_enabled is not None:
        current.post_workout_feedback_enabled = request.post_workout_feedback_enabled
    if request.post_workout_rpe_enabled is not None:
        current.post_workout_rpe_enabled = request.post_workout_rpe_enabled
    if request.post_workout_pain_enabled is not None:
        current.post_workout_pain_enabled = request.post_workout_pain_enabled
    if request.post_workout_session_feel_enabled is not None:
        current.post_workout_session_feel_enabled = request.post_workout_session_feel_enabled
    if request.post_workout_notes_enabled is not None:
        current.post_workout_notes_enabled = request.post_workout_notes_enabled

    updated = repo.update_user_settings(current)
    return UserSettingsResponse(
        id=updated.id,
        morning_checkin_enabled=updated.morning_checkin_enabled,
        morning_sleep_quality_enabled=updated.morning_sleep_quality_enabled,
        morning_sleep_hours_enabled=updated.morning_sleep_hours_enabled,
        morning_muscle_soreness_enabled=updated.morning_muscle_soreness_enabled,
        morning_energy_enabled=updated.morning_energy_enabled,
        morning_mood_enabled=updated.morning_mood_enabled,
        post_workout_feedback_enabled=updated.post_workout_feedback_enabled,
        post_workout_rpe_enabled=updated.post_workout_rpe_enabled,
        post_workout_pain_enabled=updated.post_workout_pain_enabled,
        post_workout_session_feel_enabled=updated.post_workout_session_feel_enabled,
        post_workout_notes_enabled=updated.post_workout_notes_enabled,
    )


# --- Morning Check-in ---


@router.get("/morning-checkin/{checkin_date}", response_model=MorningCheckinResponse | None)
async def get_morning_checkin(
    checkin_date: date,
    repo: Repository = Depends(get_repo),
):
    """Get morning check-in for a specific date."""
    checkin = repo.get_morning_checkin(checkin_date)
    if not checkin:
        return None
    return MorningCheckinResponse(
        id=checkin.id,
        checkin_date=checkin.checkin_date,
        sleep_quality=checkin.sleep_quality,
        sleep_hours=checkin.sleep_hours,
        muscle_soreness=checkin.muscle_soreness,
        energy_level=checkin.energy_level,
        mood=checkin.mood,
        notes=checkin.notes,
        created_at=checkin.created_at,
    )


@router.post("/morning-checkin", response_model=MorningCheckinResponse)
async def create_morning_checkin(
    request: MorningCheckinRequest,
    repo: Repository = Depends(get_repo),
):
    """Create or update morning check-in for a date."""
    checkin = MorningCheckin(
        checkin_date=request.checkin_date,
        sleep_quality=request.sleep_quality,
        sleep_hours=request.sleep_hours,
        muscle_soreness=request.muscle_soreness,
        energy_level=request.energy_level,
        mood=request.mood,
        notes=request.notes,
    )
    saved = repo.upsert_morning_checkin(checkin)
    return MorningCheckinResponse(
        id=saved.id,
        checkin_date=saved.checkin_date,
        sleep_quality=saved.sleep_quality,
        sleep_hours=saved.sleep_hours,
        muscle_soreness=saved.muscle_soreness,
        energy_level=saved.energy_level,
        mood=saved.mood,
        notes=saved.notes,
        created_at=saved.created_at,
    )


# --- Pending Feedback ---


@router.get("/pending-feedback", response_model=PendingFeedbackResponse)
async def get_pending_feedback(repo: Repository = Depends(get_repo)):
    """Get pending feedback items (activities without feedback from last 3 days + today's morning check-in)."""
    settings = repo.get_user_settings()

    # Get activities without feedback (only if post-workout feedback is enabled)
    activities = []
    if settings.post_workout_feedback_enabled:
        pending_activities = repo.get_activities_without_feedback(days=3)
        activities = [
            PendingActivityItem(
                id=a.id,
                activity_type=a.activity_type,
                title=a.title,
                start_time=a.start_time,
                duration_seconds=a.duration_seconds,
                distance_meters=a.distance_meters,
            )
            for a in pending_activities
        ]

    # Check if today's morning check-in is pending (only if morning check-in is enabled)
    morning_checkin_pending = False
    if settings.morning_checkin_enabled:
        today_checkin = repo.get_morning_checkin(date.today())
        morning_checkin_pending = today_checkin is None

    total_count = len(activities) + (1 if morning_checkin_pending else 0)

    return PendingFeedbackResponse(
        activities=activities,
        morning_checkin_pending=morning_checkin_pending,
        total_count=total_count,
    )


# --- Activity Feedback ---


@router.get("/activity-feedback/{activity_id}", response_model=ActivityFeedbackResponse | None)
async def get_activity_feedback(
    activity_id: int,
    repo: Repository = Depends(get_repo),
):
    """Get feedback for a specific activity."""
    feedback = repo.get_feedback_for_activity(activity_id)
    if not feedback:
        return None
    return ActivityFeedbackResponse(
        id=feedback.id,
        activity_id=activity_id,
        rpe=feedback.rpe,
        comfort_level=feedback.comfort_level,
        has_pain=feedback.has_pain,
        pain_location=feedback.pain_location,
        pain_severity=feedback.pain_severity,
        notes=feedback.notes,
        created_at=feedback.created_at,
    )


@router.post("/activity-feedback/{activity_id}", response_model=ActivityFeedbackResponse)
async def submit_activity_feedback(
    activity_id: int,
    request: ActivityFeedbackRequest,
    repo: Repository = Depends(get_repo),
):
    """Submit feedback for an activity."""
    # Verify activity exists
    activity = repo.get_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    feedback = WorkoutFeedback(
        activity_id=activity_id,
        rpe=request.rpe,
        comfort_level=request.comfort_level,
        has_pain=request.has_pain,
        pain_location=request.pain_location,
        pain_severity=request.pain_severity,
        notes=request.notes,
    )
    saved = repo.upsert_activity_feedback(feedback)
    return ActivityFeedbackResponse(
        id=saved.id,
        activity_id=activity_id,
        rpe=saved.rpe,
        comfort_level=saved.comfort_level,
        has_pain=saved.has_pain,
        pain_location=saved.pain_location,
        pain_severity=saved.pain_severity,
        notes=saved.notes,
        created_at=saved.created_at,
    )
