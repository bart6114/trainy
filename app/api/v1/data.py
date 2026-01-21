"""Data management API endpoints."""

from fastapi import APIRouter, Depends

from trainy.database import Repository
from app.dependencies import get_repo
from app.api.schemas.common import DataStats, DeleteResponse

router = APIRouter()


@router.get("/stats", response_model=DataStats)
async def get_data_stats(repo: Repository = Depends(get_repo)):
    """Get counts of all data types for deletion confirmation."""
    stats = repo.get_data_stats()
    return DataStats(**stats)


@router.delete("/all", response_model=DeleteResponse)
async def delete_all_data(repo: Repository = Depends(get_repo)):
    """Delete all user data except profile settings."""
    deleted = repo.delete_all_user_data()
    total = sum(deleted.values())
    return DeleteResponse(
        success=True,
        deleted=deleted,
        message=f"Deleted {total} records",
    )


@router.delete("/activities", response_model=DeleteResponse)
async def delete_all_activities(repo: Repository = Depends(get_repo)):
    """Delete all activities and related metrics/feedback."""
    deleted = repo.delete_activities_only()
    total = sum(deleted.values())
    return DeleteResponse(
        success=True,
        deleted=deleted,
        message=f"Deleted {total} records",
    )


@router.delete("/planned-workouts", response_model=DeleteResponse)
async def delete_all_planned_workouts(repo: Repository = Depends(get_repo)):
    """Delete all planned workouts."""
    count = repo.delete_all_planned_workouts()
    return DeleteResponse(
        success=True,
        deleted={"planned_workouts": count},
        message=f"Deleted {count} planned workouts",
    )
