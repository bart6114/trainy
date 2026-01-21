"""Adherence tracking API endpoints."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from trainy.database import Repository
from trainy.adherence import AdherenceTracker
from app.dependencies import get_repo

router = APIRouter()


class ReconcileResponse(BaseModel):
    """Response for reconciliation."""

    days_processed: int
    matches_found: int
    matches: list[dict]


class AdherenceStatsResponse(BaseModel):
    """Response for adherence stats."""

    total: int
    completed: int
    skipped: int
    pending: int
    completion_rate: float


@router.post("/reconcile", response_model=ReconcileResponse)
async def reconcile_activities(
    days: int = Query(default=7, ge=1, le=90, description="Number of past days to reconcile"),
    repo: Repository = Depends(get_repo),
):
    """Run reconciliation to match activities with planned workouts."""
    tracker = AdherenceTracker(repo)
    all_matches = []

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    current = start_date
    while current <= end_date:
        matches = tracker.reconcile_date(current)
        for workout_id, activity_id, score in matches:
            all_matches.append({
                "date": current.isoformat(),
                "workout_id": workout_id,
                "activity_id": activity_id,
                "score": round(score, 2),
            })
        current += timedelta(days=1)

    return ReconcileResponse(
        days_processed=days,
        matches_found=len(all_matches),
        matches=all_matches,
    )


@router.get("/stats", response_model=AdherenceStatsResponse)
async def get_adherence_stats(
    days: int = Query(default=30, ge=1, le=365, description="Number of past days to include"),
    repo: Repository = Depends(get_repo),
):
    """Get adherence statistics for the specified period."""
    tracker = AdherenceTracker(repo)

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    stats = tracker.get_adherence_stats(start_date, end_date)
    return AdherenceStatsResponse(**stats)
