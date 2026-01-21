"""API v1 router aggregation."""

from fastapi import APIRouter

from . import activities, metrics, profile, calendar, planned_workouts, adherence, import_, data, analytics, wellness

api_v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

api_v1_router.include_router(activities.router, prefix="/activities", tags=["activities"])
api_v1_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_v1_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_v1_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_v1_router.include_router(planned_workouts.router, prefix="/planned-workouts", tags=["planned-workouts"])
api_v1_router.include_router(adherence.router, prefix="/adherence", tags=["adherence"])
api_v1_router.include_router(import_.router, prefix="/import", tags=["import"])
api_v1_router.include_router(data.router, prefix="/data", tags=["data"])
api_v1_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_v1_router.include_router(wellness.router, prefix="/wellness", tags=["wellness"])

__all__ = ["api_v1_router"]
