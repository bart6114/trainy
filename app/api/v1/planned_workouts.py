"""Planned workouts API endpoints - simplified, no plan grouping."""

import asyncio
import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import StreamingResponse

from trainy.database import Repository
from trainy.database.models import PlannedWorkout
from trainy.ai.openrouter import generate_workouts_with_context, analyze_before_generation
from trainy.config import settings
from app.dependencies import get_repo
from app.api.schemas.planned_workouts import (
    PlannedWorkoutResponse,
    GeneratedWorkoutsResponse,
    UpcomingWorkoutsResponse,
    DateWorkoutsResponse,
    GenerateStreamRequest,
    RefineStreamRequest,
    AcceptProposalRequest,
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
    workout = repo.get_planned_workout_by_id(workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    repo.update_planned_workout_status(workout_id, "skipped")
    return SuccessResponse(success=True, message="Workout marked as skipped")


def _sse_event(event_type: str, data: dict) -> str:
    """Format an SSE event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def _get_training_context(repo: Repository) -> tuple[list[dict], dict, list[dict]]:
    """Get recent activities, current fitness, and existing planned workouts."""
    # Get recent activities
    recent_activities = repo.get_recent_activities_with_metrics(days=60)
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

    # Get current fitness
    latest_metrics = repo.get_latest_daily_metrics()
    current_fitness = {
        "ctl": latest_metrics.ctl if latest_metrics else 0,
        "atl": latest_metrics.atl if latest_metrics else 0,
        "tsb": latest_metrics.tsb if latest_metrics else 0,
        "tss_7day": latest_metrics.tss_7day if latest_metrics else 0,
        "tss_30day": latest_metrics.tss_30day if latest_metrics else 0,
    }

    # Get existing planned workouts (next 30 days)
    existing_workouts = repo.get_upcoming_planned_workouts(days=30)
    existing_summary = [
        {
            "date": w.planned_date.isoformat(),
            "activity_type": w.activity_type,
            "workout_type": w.workout_type,
            "title": w.title,
            "target_duration_min": round(w.target_duration_s / 60) if w.target_duration_s else None,
        }
        for w in existing_workouts
        if w.status == "planned"
    ]

    return recent_summary, current_fitness, existing_summary


@router.post("/generate/stream")
async def generate_workouts_stream(
    request: GenerateStreamRequest,
    repo: Repository = Depends(get_repo),
):
    """Generate workouts with SSE streaming for thinking indicators."""
    if not settings.has_openrouter_key:
        raise HTTPException(status_code=400, detail="OpenRouter API key not configured")

    async def event_generator():
        try:
            # Phase 1: Analyzing
            yield _sse_event("thinking", {"phase": "analyzing", "message": "Analyzing your request..."})

            # Gather context
            recent_summary, current_fitness, existing_workouts = _get_training_context(repo)

            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

            # Run analysis to check if clarification needed
            analysis = await analyze_before_generation(
                user_prompt=request.prompt,
                recent_activities=recent_summary,
                current_fitness=current_fitness,
                existing_workouts=existing_workouts,
                conversation_history=conversation_history,
            )

            # If analysis failed, proceed to generation anyway
            if analysis is not None and not analysis.ready_to_generate:
                # AI wants to ask a question
                yield _sse_event("question", {
                    "message": analysis.clarifying_question,
                    "options": analysis.question_options,
                })
                return

            # Phase 2: Generating
            yield _sse_event("thinking", {"phase": "generating", "message": "Creating personalized workouts..."})

            # Generate workouts with conversation context
            result = await generate_workouts_with_context(
                user_prompt=request.prompt,
                recent_activities=recent_summary,
                current_fitness=current_fitness,
                existing_workouts=existing_workouts,
                conversation_history=conversation_history,
            )

            if result is None:
                yield _sse_event("error", {"message": "Failed to generate workouts"})
                return

            workouts, assistant_message = result

            # Convert to proposal format
            proposal = [
                {
                    "date": w.planned_date.isoformat(),
                    "activity_type": w.activity_type,
                    "workout_type": w.workout_type,
                    "title": w.title,
                    "description": w.description,
                    "target_duration_minutes": round(w.target_duration_s / 60) if w.target_duration_s else 0,
                    "target_tss": w.target_tss,
                }
                for w in workouts
            ]

            yield _sse_event("proposal", {
                "workouts": proposal,
                "assistant_message": assistant_message,
            })

        except Exception as e:
            yield _sse_event("error", {"message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/refine/stream")
async def refine_workouts_stream(
    request: RefineStreamRequest,
    repo: Repository = Depends(get_repo),
):
    """Refine a workout proposal with SSE streaming."""
    if not settings.has_openrouter_key:
        raise HTTPException(status_code=400, detail="OpenRouter API key not configured")

    async def event_generator():
        try:
            # Phase 1: Analyzing refinement
            yield _sse_event("thinking", {"phase": "analyzing", "message": "Understanding your feedback..."})
            await asyncio.sleep(0.3)

            # Gather context
            recent_summary, current_fitness, existing_workouts = _get_training_context(repo)

            # Phase 2: Refining
            yield _sse_event("thinking", {"phase": "generating", "message": "Refining your workout plan..."})

            # Build conversation history including current proposal context
            full_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

            # Add current proposal as context
            proposal_context = "Current workout proposal:\n" + "\n".join(
                f"- {w.date}: {w.title} ({w.activity_type}/{w.workout_type}) - {w.target_duration_minutes}min"
                for w in request.current_proposal
            )

            # Generate refined workouts
            result = await generate_workouts_with_context(
                user_prompt=f"{proposal_context}\n\nUser refinement request: {request.refinement}",
                recent_activities=recent_summary,
                current_fitness=current_fitness,
                existing_workouts=existing_workouts,
                conversation_history=full_history,
                is_refinement=True,
            )

            if result is None:
                yield _sse_event("error", {"message": "Failed to refine workouts"})
                return

            workouts, assistant_message = result

            # Convert to proposal format
            proposal = [
                {
                    "date": w.planned_date.isoformat(),
                    "activity_type": w.activity_type,
                    "workout_type": w.workout_type,
                    "title": w.title,
                    "description": w.description,
                    "target_duration_minutes": round(w.target_duration_s / 60) if w.target_duration_s else 0,
                    "target_tss": w.target_tss,
                }
                for w in workouts
            ]

            yield _sse_event("proposal", {
                "workouts": proposal,
                "assistant_message": assistant_message,
            })

        except Exception as e:
            yield _sse_event("error", {"message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/accept", response_model=GeneratedWorkoutsResponse)
async def accept_proposal(
    request: AcceptProposalRequest,
    repo: Repository = Depends(get_repo),
):
    """Accept and save a workout proposal to the database."""
    saved_workouts = []

    for workout in request.workouts:
        planned_workout = PlannedWorkout(
            planned_date=workout.date,
            activity_type=workout.activity_type,
            workout_type=workout.workout_type,
            title=workout.title,
            description=workout.description,
            target_duration_s=workout.target_duration_minutes * 60 if workout.target_duration_minutes else None,
            target_tss=workout.target_tss,
            status="planned",
        )
        workout_id = repo.insert_planned_workout(planned_workout)
        planned_workout.id = workout_id
        saved_workouts.append(planned_workout)

    return GeneratedWorkoutsResponse(
        workouts=[_workout_to_response(w) for w in saved_workouts],
        count=len(saved_workouts),
    )
