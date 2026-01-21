"""Planned workouts API endpoints - simplified, no plan grouping."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Path

from trainy.database import Repository
from trainy.database.models import PlannedWorkout
from trainy.ai.openrouter import generate_workouts
from trainy.config import settings
from app.dependencies import get_repo
from app.api.schemas.planned_workouts import (
    PlannedWorkoutResponse,
    GenerateWorkoutsRequest,
    GeneratedWorkoutsResponse,
    UpcomingWorkoutsResponse,
    DateWorkoutsResponse,
)
from app.api.schemas.common import SuccessResponse

router = APIRouter()


def _workout_to_response(workout: PlannedWorkout) -> PlannedWorkoutResponse:
    """Convert PlannedWorkout to response model."""
    return PlannedWorkoutResponse(
        id=workout.id,
        planned_date=workout.planned_date,
        activity_type=workout.activity_type,
        workout_type=workout.workout_type,
        title=workout.title,
        description=workout.description,
        structured_workout=workout.structured_workout,
        target_duration_s=workout.target_duration_s,
        target_distance_m=workout.target_distance_m,
        target_tss=workout.target_tss,
        target_hr_zone=workout.target_hr_zone,
        target_pace_minkm=workout.target_pace_minkm,
        status=workout.status,
        completed_activity_id=workout.completed_activity_id,
        created_at=workout.created_at,
    )


@router.post("/generate", response_model=GeneratedWorkoutsResponse)
async def generate_planned_workouts(
    request: GenerateWorkoutsRequest,
    repo: Repository = Depends(get_repo),
):
    """Generate and immediately save planned workouts using AI."""
    if not settings.has_openrouter_key:
        raise HTTPException(status_code=400, detail="OpenRouter API key not configured")

    # Get recent activities and current fitness for context
    recent_activities = repo.get_recent_activities_with_metrics(days=60)
    latest_metrics = repo.get_latest_daily_metrics()

    # Convert activities to enriched summary format
    recent_summary = [
        {
            "date": a.start_time.strftime("%Y-%m-%d"),
            "type": a.activity_type,
            "duration_min": round(a.duration_seconds / 60) if a.duration_seconds else 0,
            "distance_km": round(a.distance_meters / 1000, 1) if a.distance_meters else 0,
            "avg_hr": a.avg_hr,
            "max_hr": a.max_hr,
            "avg_power": a.avg_power,
            "elevation_m": a.total_ascent_m,
            "cadence": a.avg_cadence,
            "tss": a.tss,
        }
        for a in recent_activities
    ]

    current_fitness = {
        "ctl": latest_metrics.ctl if latest_metrics else 0,
        "atl": latest_metrics.atl if latest_metrics else 0,
        "tsb": latest_metrics.tsb if latest_metrics else 0,
        "tss_7day": latest_metrics.tss_7day if latest_metrics else 0,
        "tss_30day": latest_metrics.tss_30day if latest_metrics else 0,
    }

    # Generate workouts via AI
    workouts = await generate_workouts(
        user_prompt=request.prompt,
        recent_activities=recent_summary,
        current_fitness=current_fitness,
    )

    if not workouts:
        raise HTTPException(status_code=500, detail="Failed to generate workouts")

    # Save workouts immediately
    saved_workouts = []
    for workout in workouts:
        workout_id = repo.insert_planned_workout(workout)
        workout.id = workout_id
        saved_workouts.append(workout)

    return GeneratedWorkoutsResponse(
        workouts=[_workout_to_response(w) for w in saved_workouts],
        count=len(saved_workouts),
    )


@router.get("/upcoming", response_model=UpcomingWorkoutsResponse)
async def get_upcoming_workouts(
    days: int = 7,
    repo: Repository = Depends(get_repo),
):
    """Get upcoming planned workouts for the next N days."""
    workouts = repo.get_upcoming_planned_workouts(days=days)
    return UpcomingWorkoutsResponse(
        workouts=[_workout_to_response(w) for w in workouts],
        days=days,
    )


@router.get("/date/{date_str}", response_model=DateWorkoutsResponse)
async def get_workouts_for_date(
    date_str: str = Path(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    repo: Repository = Depends(get_repo),
):
    """Get planned workouts for a specific date."""
    target_date = date.fromisoformat(date_str)
    workouts = repo.get_planned_workouts_for_date(target_date)
    return DateWorkoutsResponse(
        date=target_date,
        workouts=[_workout_to_response(w) for w in workouts],
    )


@router.delete("/{workout_id}", response_model=SuccessResponse)
async def delete_workout(
    workout_id: int,
    repo: Repository = Depends(get_repo),
):
    """Delete a planned workout."""
    deleted = repo.delete_planned_workout(workout_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workout not found")
    return SuccessResponse(success=True, message="Workout deleted")


@router.patch("/{workout_id}/skip", response_model=SuccessResponse)
async def skip_workout(
    workout_id: int,
    repo: Repository = Depends(get_repo),
):
    """Mark a workout as skipped."""
    # Check if workout exists
    workouts = repo.get_planned_workouts_range(date.min, date.max)
    workout = next((w for w in workouts if w.id == workout_id), None)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    repo.update_planned_workout_status(workout_id, "skipped")
    return SuccessResponse(success=True, message="Workout marked as skipped")
