"""Activities API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query

from trainy.database import Repository
from app.dependencies import get_repo
from app.api.schemas.activities import (
    ActivityResponse,
    ActivityWithMetricsResponse,
    ActivityListResponse,
    ActivityMetricsResponse,
)

router = APIRouter()


@router.get("", response_model=ActivityListResponse)
async def list_activities(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: Repository = Depends(get_repo),
):
    """List activities with pagination."""
    total = repo.get_activity_count()
    activities = repo.get_all_activities(limit=limit, offset=offset)

    items = [
        ActivityResponse(
            id=a.id,
            fit_file_hash=a.fit_file_hash,
            start_time=a.start_time,
            end_time=a.end_time,
            activity_type=a.activity_type,
            source=a.source,
            duration_seconds=a.duration_seconds,
            distance_meters=a.distance_meters,
            avg_speed_mps=a.avg_speed_mps,
            max_speed_mps=a.max_speed_mps,
            total_ascent_m=a.total_ascent_m,
            total_descent_m=a.total_descent_m,
            avg_hr=a.avg_hr,
            max_hr=a.max_hr,
            avg_power=a.avg_power,
            max_power=a.max_power,
            normalized_power=a.normalized_power,
            avg_cadence=a.avg_cadence,
            calories=a.calories,
            title=a.title,
            imported_at=a.imported_at,
        )
        for a in activities
    ]

    return ActivityListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/{activity_id}", response_model=ActivityWithMetricsResponse)
async def get_activity(
    activity_id: int,
    repo: Repository = Depends(get_repo),
):
    """Get a single activity with its metrics."""
    activity = repo.get_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    metrics = repo.get_activity_metrics(activity_id)

    activity_response = ActivityResponse(
        id=activity.id,
        fit_file_hash=activity.fit_file_hash,
        start_time=activity.start_time,
        end_time=activity.end_time,
        activity_type=activity.activity_type,
        source=activity.source,
        duration_seconds=activity.duration_seconds,
        distance_meters=activity.distance_meters,
        avg_speed_mps=activity.avg_speed_mps,
        max_speed_mps=activity.max_speed_mps,
        total_ascent_m=activity.total_ascent_m,
        total_descent_m=activity.total_descent_m,
        avg_hr=activity.avg_hr,
        max_hr=activity.max_hr,
        avg_power=activity.avg_power,
        max_power=activity.max_power,
        normalized_power=activity.normalized_power,
        avg_cadence=activity.avg_cadence,
        calories=activity.calories,
        title=activity.title,
        imported_at=activity.imported_at,
    )

    metrics_response = None
    if metrics:
        metrics_response = ActivityMetricsResponse(
            activity_id=metrics.activity_id,
            tss=metrics.tss,
            tss_method=metrics.tss_method,
            intensity_factor=metrics.intensity_factor,
            efficiency_factor=metrics.efficiency_factor,
            variability_index=metrics.variability_index,
            peak_power_5s=metrics.peak_power_5s,
            peak_power_1min=metrics.peak_power_1min,
            peak_power_5min=metrics.peak_power_5min,
            peak_power_20min=metrics.peak_power_20min,
            calculated_at=metrics.calculated_at,
        )

    return ActivityWithMetricsResponse(
        activity=activity_response,
        metrics=metrics_response,
    )
