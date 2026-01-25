"""Coaching API endpoints with tool-calling."""

import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from trainy.database import Repository
from trainy.database.models import PlannedWorkout
from trainy.ai.coaching import run_coaching_conversation
from trainy.config import settings
from app.dependencies import get_repo
from app.api.schemas.coaching import (
    CoachingChatRequest,
    AcceptCoachingProposalRequest,
    AcceptCoachingProposalResponse,
)

router = APIRouter()


def _sse_event(event_type: str, data: dict) -> str:
    """Format an SSE event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@router.post("/chat/stream")
async def coaching_chat_stream(
    request: CoachingChatRequest,
    repo: Repository = Depends(get_repo),
):
    """Stream a coaching conversation with tool-calling.

    SSE Events:
    - thinking: {message: str} - AI is processing
    - tool_call: {tool_name: str, arguments: dict} - AI is calling a tool
    - tool_result: {tool_name: str, result: dict, summary: str} - Tool execution result
    - text: {content: str} - AI text response
    - proposal: {workouts: list, deletions: list, proposal_id: str} - Workout proposal
    - error: {message: str} - Error occurred
    """
    if not settings.has_openrouter_key:
        raise HTTPException(status_code=400, detail="OpenRouter API key not configured")

    async def event_generator():
        try:
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

            async for event in run_coaching_conversation(
                message=request.message,
                conversation_history=conversation_history,
                repo=repo,
            ):
                event_type = event.get("event", "")
                event_data = event.get("data", {})
                yield _sse_event(event_type, event_data)

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


@router.post("/accept-proposal", response_model=AcceptCoachingProposalResponse)
async def accept_coaching_proposal(
    request: AcceptCoachingProposalRequest,
    repo: Repository = Depends(get_repo),
):
    """Accept a coaching proposal, creating/updating/deleting workouts."""
    created_ids = []
    updated_ids = []
    deleted_ids = []

    # Process workout creations and updates
    for workout in request.workouts:
        if workout.existing_workout_id:
            # Update existing workout
            updated = repo.update_planned_workout(
                workout_id=workout.existing_workout_id,
                planned_date=date.fromisoformat(workout.date),
                activity_type=workout.activity_type,
                workout_type=workout.workout_type,
                title=workout.title,
                description=workout.description,
                target_duration_s=workout.target_duration_minutes * 60 if workout.target_duration_minutes else None,
                target_tss=workout.target_tss,
                target_calories=workout.target_calories,
            )
            if updated:
                updated_ids.append(workout.existing_workout_id)
        else:
            # Create new workout
            planned_workout = PlannedWorkout(
                planned_date=date.fromisoformat(workout.date),
                activity_type=workout.activity_type,
                workout_type=workout.workout_type,
                title=workout.title,
                description=workout.description,
                target_duration_s=workout.target_duration_minutes * 60 if workout.target_duration_minutes else None,
                target_tss=workout.target_tss,
                target_calories=workout.target_calories,
                status="planned",
            )
            workout_id = repo.insert_planned_workout(planned_workout)
            created_ids.append(workout_id)

    # Process deletions
    for deletion in request.deletions:
        if repo.delete_planned_workout(deletion.workout_id):
            deleted_ids.append(deletion.workout_id)

    # Build message
    parts = []
    if created_ids:
        parts.append(f"{len(created_ids)} created")
    if updated_ids:
        parts.append(f"{len(updated_ids)} updated")
    if deleted_ids:
        parts.append(f"{len(deleted_ids)} deleted")

    message = "Workouts " + ", ".join(parts) if parts else "No changes made"

    return AcceptCoachingProposalResponse(
        created_ids=created_ids,
        updated_ids=updated_ids,
        deleted_ids=deleted_ids,
        message=message,
    )
