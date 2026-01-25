"""Analytics API endpoints."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query

from trainy.database import Repository
from trainy.metrics.critical_power import estimate_ftp_with_fallback
from app.dependencies import get_repo

from app.api.schemas.analytics import (
    PowerCurveResponse,
    PowerCurvePoint,
    InjuryAnalysisResponse,
    PainEvent,
    PainLocationSummary,
    PainActivitySummary,
    PainLocationCount,
    MergePainLocationsRequest,
    MergePainLocationsResponse,
    RowingPRsResponse,
    RowingDistancePR,
    RowingTimePR,
    RowingPowerPR,
)

router = APIRouter()

# Duration configurations for power curve
DURATIONS = [
    (5, "5s"),
    (60, "1min"),
    (300, "5min"),
    (1200, "20min"),
]


@router.get("/power-curve", response_model=PowerCurveResponse)
async def get_power_curve(
    days: int = Query(90, ge=7, le=365, description="Number of days to look back"),
    repo: Repository = Depends(get_repo),
):
    """Get power curve data showing best power at various durations."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Get user profile for weight and FTP
    profile = repo.get_current_profile()
    weight_kg = profile.weight_kg or 70.0

    # Get all peak power data within the range
    power_data = repo.get_peak_powers_for_range(start_date, end_date)

    # Find best power for each duration
    best_powers = {
        5: {"watts": None, "activity_id": None, "date": None},
        60: {"watts": None, "activity_id": None, "date": None},
        300: {"watts": None, "activity_id": None, "date": None},
        1200: {"watts": None, "activity_id": None, "date": None},
    }

    column_map = {
        5: "peak_power_5s",
        60: "peak_power_1min",
        300: "peak_power_5min",
        1200: "peak_power_20min",
    }

    for row in power_data:
        for duration, column in column_map.items():
            power = row.get(column)
            if power is not None:
                current_best = best_powers[duration]["watts"]
                if current_best is None or power > current_best:
                    best_powers[duration] = {
                        "watts": power,
                        "activity_id": row.get("activity_id"),
                        "date": row.get("activity_date"),
                    }

    # Build response points
    points = []
    for duration, label in DURATIONS:
        best = best_powers[duration]
        watts = best["watts"]
        watts_per_kg = round(watts / weight_kg, 2) if watts else None

        points.append(
            PowerCurvePoint(
                duration_seconds=duration,
                duration_label=label,
                best_watts=round(watts, 1) if watts else None,
                best_watts_per_kg=watts_per_kg,
                activity_id=best["activity_id"],
                activity_date=date.fromisoformat(best["date"]) if best["date"] else None,
            )
        )

    # Collect power-duration pairs for CP model
    durations = []
    powers = []
    for duration in [5, 60, 300, 1200]:
        if best_powers[duration]["watts"]:
            durations.append(duration)
            powers.append(best_powers[duration]["watts"])

    # Calculate eFTP using CP model with fallback
    eftp, w_prime, method = estimate_ftp_with_fallback(
        durations, powers, best_powers[1200]["watts"]
    )

    return PowerCurveResponse(
        start_date=start_date,
        end_date=end_date,
        weight_kg=weight_kg,
        ftp=profile.ftp,
        eftp=eftp,
        w_prime=w_prime,
        eftp_method=method,
        points=points,
    )


@router.get("/injury-analysis", response_model=InjuryAnalysisResponse)
async def get_injury_analysis(
    days: int = Query(90, ge=7, le=365, description="Number of days to look back"),
    repo: Repository = Depends(get_repo),
):
    """Get injury analysis data showing pain events and patterns."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Get pain data from repository
    pain_events_raw = repo.get_pain_events_for_range(start_date, end_date)
    by_location_raw = repo.get_pain_summary_by_location(start_date, end_date)
    by_activity_raw = repo.get_pain_summary_by_activity_type(start_date, end_date)

    # Convert to response models
    pain_events = [
        PainEvent(
            date=date.fromisoformat(e["date"]),
            pain_location=e["pain_location"],
            pain_severity=e["pain_severity"],
            activity_type=e["activity_type"],
            activity_id=e["activity_id"],
            activity_title=e["activity_title"],
        )
        for e in pain_events_raw
    ]

    by_location = [
        PainLocationSummary(
            location=loc["location"],
            count=loc["count"],
            avg_severity=loc["avg_severity"],
            max_severity=loc["max_severity"],
        )
        for loc in by_location_raw
    ]

    by_activity = [
        PainActivitySummary(
            activity_type=act["activity_type"],
            count=act["count"],
            avg_severity=act["avg_severity"],
        )
        for act in by_activity_raw
    ]

    return InjuryAnalysisResponse(
        start_date=start_date,
        end_date=end_date,
        total_pain_events=len(pain_events),
        pain_events=pain_events,
        by_location=by_location,
        by_activity=by_activity,
    )


@router.get("/pain-locations", response_model=list[PainLocationCount])
async def get_pain_locations(
    repo: Repository = Depends(get_repo),
):
    """Get all unique pain locations with occurrence counts."""
    locations_raw = repo.get_unique_pain_locations()
    return [
        PainLocationCount(location=loc["location"], count=loc["count"])
        for loc in locations_raw
    ]


@router.post("/merge-pain-locations", response_model=MergePainLocationsResponse)
async def merge_pain_locations(
    request: MergePainLocationsRequest,
    repo: Repository = Depends(get_repo),
):
    """Merge multiple pain locations into a single target location."""
    updated_count = repo.merge_pain_locations(
        sources=request.source_locations,
        target=request.target_location,
    )
    return MergePainLocationsResponse(updated_count=updated_count)


@router.get("/rowing-prs", response_model=RowingPRsResponse)
async def get_rowing_prs(
    days: int = Query(90, ge=7, le=365, description="Number of days to look back"),
    repo: Repository = Depends(get_repo),
):
    """Get rowing personal records for standard distances and time durations.

    Data is pre-computed during metrics recalculation and stored in the database.
    Uses the days parameter to filter by date range (similar to power-curve endpoint).
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Query pre-computed rowing PRs from database
    prs = repo.get_rowing_prs_for_range(start_date, end_date)

    # Build distance PRs response with split calculation
    distance_prs = []
    for pr in prs["distance_prs"]:
        total_seconds = pr["total_seconds"]
        split_seconds = None
        if total_seconds is not None:
            split_seconds = (total_seconds / pr["distance_meters"]) * 500

        distance_prs.append(
            RowingDistancePR(
                distance_meters=pr["distance_meters"],
                distance_label=pr["distance_label"],
                total_seconds=total_seconds,
                split_seconds=round(split_seconds, 1) if split_seconds else None,
                activity_id=pr["activity_id"],
                activity_date=date.fromisoformat(pr["activity_date"]) if pr["activity_date"] else None,
            )
        )

    # Build time PRs response with split calculation
    time_prs = []
    for pr in prs["time_prs"]:
        best_distance = pr["best_distance_meters"]
        split_seconds = None
        if best_distance is not None and best_distance > 0:
            split_seconds = (pr["duration_seconds"] / best_distance) * 500

        time_prs.append(
            RowingTimePR(
                duration_seconds=pr["duration_seconds"],
                duration_label=pr["duration_label"],
                best_distance_meters=best_distance,
                split_seconds=round(split_seconds, 1) if split_seconds else None,
                activity_id=pr["activity_id"],
                activity_date=date.fromisoformat(pr["activity_date"]) if pr["activity_date"] else None,
            )
        )

    # Build power PRs response
    power_prs = []
    for pr in prs["power_prs"]:
        power_prs.append(
            RowingPowerPR(
                duration_seconds=pr["duration_seconds"],
                duration_label=pr["duration_label"],
                best_watts=round(pr["best_watts"], 1) if pr["best_watts"] else None,
                activity_id=pr["activity_id"],
                activity_date=date.fromisoformat(pr["activity_date"]) if pr["activity_date"] else None,
            )
        )

    return RowingPRsResponse(
        distance_prs=distance_prs,
        time_prs=time_prs,
        power_prs=power_prs,
    )
