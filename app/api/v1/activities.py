"""Activities API endpoints."""

import gzip
import json

from fastapi import APIRouter, Depends, HTTPException, Query

from trainy.database import Repository
from trainy.metrics.calories import predict_calories
from app.dependencies import get_repo
from app.api.schemas.activities import (
    ActivityResponse,
    ActivityWithMetricsResponse,
    ActivityListResponse,
    ActivityMetricsResponse,
    ActivityTrackResponse,
    TrackPoint,
)

router = APIRouter()


def _estimate_calories(
    activity,
    repo: Repository,
    profile_weight_kg: float | None,
) -> int | None:
    """Estimate calories for an activity if not available from FIT file."""
    if activity.calories is not None:
        return activity.calories

    if not activity.duration_seconds or activity.duration_seconds <= 0:
        return None

    if not profile_weight_kg or profile_weight_kg <= 0:
        return None

    # Get intensity factor from activity metrics if available
    metrics = repo.get_activity_metrics(activity.id)
    intensity_factor = metrics.intensity_factor if metrics and metrics.intensity_factor else 0.75

    return predict_calories(
        duration_s=activity.duration_seconds,
        activity_type=activity.activity_type or "other",
        intensity_factor=intensity_factor,
        weight_kg=profile_weight_kg,
    )


@router.get("", response_model=ActivityListResponse)
async def list_activities(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: Repository = Depends(get_repo),
):
    """List activities with pagination."""
    total = repo.get_activity_count()
    activities = repo.get_all_activities(limit=limit, offset=offset)

    # Get user profile for calorie estimation
    profile = repo.get_current_profile()
    profile_weight_kg = profile.weight_kg if profile else None

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
            calories=_estimate_calories(a, repo, profile_weight_kg),
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

    # Get user profile for calorie estimation
    profile = repo.get_current_profile()
    profile_weight_kg = profile.weight_kg if profile else None

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
        calories=_estimate_calories(activity, repo, profile_weight_kg),
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


def _semicircles_to_degrees(semicircles: int | float) -> float:
    """Convert FIT file semicircles to degrees.

    FIT files store coordinates in semicircles: degrees = semicircles * (180 / 2^31)
    """
    return semicircles * (180.0 / 2147483648.0)


@router.get("/{activity_id}/track", response_model=ActivityTrackResponse)
async def get_activity_track(
    activity_id: int,
    repo: Repository = Depends(get_repo),
):
    """Get GPS track data for an activity."""
    activity = repo.get_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if not activity.raw_fit_data:
        return ActivityTrackResponse(
            activity_id=activity_id,
            has_track=False,
            points=[],
        )

    # Decompress and parse the raw FIT data
    try:
        json_str = gzip.decompress(activity.raw_fit_data).decode("utf-8")
        raw_data = json.loads(json_str)
    except (gzip.BadGzipFile, json.JSONDecodeError):
        return ActivityTrackResponse(
            activity_id=activity_id,
            has_track=False,
            points=[],
        )

    records = raw_data.get("records", [])
    points = []

    for record in records:
        lat = record.get("position_lat")
        lng = record.get("position_long")

        if lat is not None and lng is not None:
            # Convert from semicircles to degrees
            lat_deg = _semicircles_to_degrees(lat)
            lng_deg = _semicircles_to_degrees(lng)

            # Validate coordinates are in valid range
            if -90 <= lat_deg <= 90 and -180 <= lng_deg <= 180:
                points.append(TrackPoint(lat=lat_deg, lng=lng_deg))

    return ActivityTrackResponse(
        activity_id=activity_id,
        has_track=len(points) > 0,
        points=points,
    )
