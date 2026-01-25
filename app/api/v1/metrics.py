"""Metrics API endpoints."""

import asyncio
import json
from datetime import date, timedelta
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, Depends, Query, HTTPException
from sse_starlette.sse import EventSourceResponse

from trainy.database import Repository
from trainy.database.models import ActivityMetrics
from trainy.metrics import calculate_tss
from trainy.metrics.training_load import calculate_training_load
from trainy.metrics.efficiency import calculate_efficiency_factor, calculate_variability_index
from trainy.importers.fit_importer import (
    extract_power_samples_from_fit,
    calculate_all_peak_powers,
    extract_distance_time_series,
    calculate_best_effort_time,
    calculate_best_effort_distance,
)
from app.dependencies import get_repo
from app.api.schemas.metrics import (
    CurrentMetricsResponse,
    DailyMetricsResponse,
    DailyMetricsItem,
    WeeklyTSSResponse,
    WeeklyTSSItem,
)
from app.api.schemas.common import SuccessResponse

router = APIRouter()


@router.get("/current", response_model=CurrentMetricsResponse)
async def get_current_metrics(
    repo: Repository = Depends(get_repo),
):
    """Get current training metrics (CTL/ATL/TSB/ACWR)."""
    latest = repo.get_latest_daily_metrics()

    if not latest:
        # Return zeros if no metrics exist
        return CurrentMetricsResponse(
            date=date.today(),
            ctl=0.0,
            atl=0.0,
            tsb=0.0,
            tss_7day=0.0,
            tss_30day=0.0,
            tss_90day=0.0,
            acwr=None,
            monotony=None,
            strain=None,
        )

    return CurrentMetricsResponse(
        date=latest.date,
        ctl=latest.ctl or 0.0,
        atl=latest.atl or 0.0,
        tsb=latest.tsb or 0.0,
        tss_7day=latest.tss_7day,
        tss_30day=latest.tss_30day,
        tss_90day=latest.tss_90day,
        acwr=latest.acwr,
        monotony=latest.monotony,
        strain=latest.strain,
    )


@router.get("/daily", response_model=DailyMetricsResponse)
async def get_daily_metrics(
    start: date = Query(None, description="Start date (default: 90 days ago)"),
    end: date = Query(None, description="End date (default: today)"),
    repo: Repository = Depends(get_repo),
):
    """Get daily metrics for a date range (for charts)."""
    if not end:
        end = date.today()
    if not start:
        start = end - timedelta(days=90)

    metrics = repo.get_daily_metrics_range(start, end)

    items = [
        DailyMetricsItem(
            date=m.date,
            total_tss=m.total_tss,
            activity_count=m.activity_count,
            total_duration_s=m.total_duration_s,
            total_distance_m=m.total_distance_m,
            ctl=m.ctl,
            atl=m.atl,
            tsb=m.tsb,
            acwr=m.acwr,
            monotony=m.monotony,
            strain=m.strain,
        )
        for m in metrics
    ]

    return DailyMetricsResponse(
        start_date=start,
        end_date=end,
        items=items,
    )


@router.get("/weekly", response_model=WeeklyTSSResponse)
async def get_weekly_tss(
    weeks: int = Query(12, ge=1, le=52),
    repo: Repository = Depends(get_repo),
):
    """Get weekly TSS totals for charts."""
    weekly_data = repo.get_weekly_tss_totals(weeks=weeks)

    items = []
    for week in weekly_data:
        week_start = date.fromisoformat(week["week_start"])
        week_end = week_start + timedelta(days=6)
        items.append(
            WeeklyTSSItem(
                week_start=week_start,
                week_end=week_end,
                total_tss=week["total_tss"],
                activity_count=0,  # Not tracked in current query
            )
        )

    return WeeklyTSSResponse(weeks=weeks, items=items)


@router.post("/recalculate", response_model=SuccessResponse)
async def recalculate_metrics(
    repo: Repository = Depends(get_repo),
):
    """Trigger full recalculation of all metrics (activity + training load)."""
    # Get user profile for TSS calculations
    profile = repo.get_current_profile()

    # Step 1: Recalculate activity metrics (TSS, EF, VI, Peak Powers)
    activities = repo.get_all_activities()
    activity_count = 0

    for activity in activities:
        # Calculate TSS
        tss, method, intensity_factor = calculate_tss(activity, profile)

        # Calculate efficiency metrics
        ef = calculate_efficiency_factor(activity)
        vi = calculate_variability_index(activity)

        # Calculate peak powers for cycling and rowing activities
        peak_powers = {}
        rowing_efforts = {}
        if activity.activity_type in ("cycle", "row") and activity.fit_file_path:
            fit_path = Path(activity.fit_file_path)
            power_samples, sample_interval = extract_power_samples_from_fit(fit_path)
            if power_samples:
                include_rowing = activity.activity_type == "row"
                peak_powers = calculate_all_peak_powers(power_samples, include_rowing=include_rowing, sample_interval=sample_interval)

            # Calculate rowing best efforts
            if activity.activity_type == "row":
                series = extract_distance_time_series(fit_path)
                if series:
                    # Distance PRs: best time to cover each distance
                    rowing_efforts["rowing_500m_time"] = calculate_best_effort_time(series, 500)
                    rowing_efforts["rowing_1k_time"] = calculate_best_effort_time(series, 1000)
                    rowing_efforts["rowing_2k_time"] = calculate_best_effort_time(series, 2000)
                    rowing_efforts["rowing_5k_time"] = calculate_best_effort_time(series, 5000)
                    rowing_efforts["rowing_10k_time"] = calculate_best_effort_time(series, 10000)
                    # Time PRs: best distance covered in each duration
                    rowing_efforts["rowing_1min_distance"] = calculate_best_effort_distance(series, 60)
                    rowing_efforts["rowing_4min_distance"] = calculate_best_effort_distance(series, 240)
                    rowing_efforts["rowing_10min_distance"] = calculate_best_effort_distance(series, 600)
                    rowing_efforts["rowing_20min_distance"] = calculate_best_effort_distance(series, 1200)
                    rowing_efforts["rowing_30min_distance"] = calculate_best_effort_distance(series, 1800)
                    rowing_efforts["rowing_60min_distance"] = calculate_best_effort_distance(series, 3600)

        # Store activity metrics
        metrics = ActivityMetrics(
            activity_id=activity.id,
            tss=tss,
            tss_method=method.value,
            intensity_factor=intensity_factor,
            efficiency_factor=ef,
            variability_index=vi,
            peak_power_5s=peak_powers.get("peak_power_5s"),
            peak_power_1min=peak_powers.get("peak_power_1min"),
            peak_power_5min=peak_powers.get("peak_power_5min"),
            peak_power_20min=peak_powers.get("peak_power_20min"),
            peak_power_4min=peak_powers.get("peak_power_4min"),
            peak_power_30min=peak_powers.get("peak_power_30min"),
            peak_power_60min=peak_powers.get("peak_power_60min"),
            rowing_500m_time=rowing_efforts.get("rowing_500m_time"),
            rowing_1k_time=rowing_efforts.get("rowing_1k_time"),
            rowing_2k_time=rowing_efforts.get("rowing_2k_time"),
            rowing_5k_time=rowing_efforts.get("rowing_5k_time"),
            rowing_10k_time=rowing_efforts.get("rowing_10k_time"),
            rowing_1min_distance=rowing_efforts.get("rowing_1min_distance"),
            rowing_4min_distance=rowing_efforts.get("rowing_4min_distance"),
            rowing_10min_distance=rowing_efforts.get("rowing_10min_distance"),
            rowing_20min_distance=rowing_efforts.get("rowing_20min_distance"),
            rowing_30min_distance=rowing_efforts.get("rowing_30min_distance"),
            rowing_60min_distance=rowing_efforts.get("rowing_60min_distance"),
        )
        repo.insert_activity_metrics(metrics)
        activity_count += 1

    # Step 2: Recalculate daily training load metrics
    daily_tss = repo.get_daily_tss_series()

    if not daily_tss:
        return SuccessResponse(
            success=True,
            message=f"Recalculated metrics for {activity_count} activities (no daily data)",
        )

    # Calculate training load (CTL/ATL/TSB/ACWR/Monotony/Strain)
    metrics_list = calculate_training_load(daily_tss)

    # Save each day's metrics
    for metrics in metrics_list:
        repo.upsert_daily_metrics(metrics)

    # Mark profile as clean
    repo.set_metrics_dirty(False)

    return SuccessResponse(
        success=True,
        message=f"Recalculated metrics for {activity_count} activities and {len(metrics_list)} days",
    )


async def recalculate_generator(repo: Repository) -> AsyncIterator[dict]:
    """Generate SSE events for metrics recalculation progress."""
    # Get user profile for TSS calculations
    profile = repo.get_current_profile()

    # Get all activities and daily TSS data upfront
    activities = list(repo.get_all_activities())
    daily_tss = repo.get_daily_tss_series()

    total_activities = len(activities)
    total_days = len(daily_tss) if daily_tss else 0

    if total_activities == 0 and total_days == 0:
        yield {
            "event": "complete",
            "data": json.dumps({
                "activities_processed": 0,
                "days_processed": 0,
            }),
        }
        await asyncio.sleep(0)
        return

    # Send start event
    yield {
        "event": "start",
        "data": json.dumps({
            "total_activities": total_activities,
            "total_days": total_days,
        }),
    }
    await asyncio.sleep(0)

    # Phase 1: Process activities (TSS, EF, VI, Peak Powers)
    for i, activity in enumerate(activities, 1):
        # Calculate TSS
        tss, method, intensity_factor = calculate_tss(activity, profile)

        # Calculate efficiency metrics
        ef = calculate_efficiency_factor(activity)
        vi = calculate_variability_index(activity)

        # Calculate peak powers for cycling and rowing activities
        peak_powers = {}
        rowing_efforts = {}
        if activity.activity_type in ("cycle", "row") and activity.fit_file_path:
            fit_path = Path(activity.fit_file_path)
            power_samples, sample_interval = extract_power_samples_from_fit(fit_path)
            if power_samples:
                include_rowing = activity.activity_type == "row"
                peak_powers = calculate_all_peak_powers(power_samples, include_rowing=include_rowing, sample_interval=sample_interval)

            # Calculate rowing best efforts
            if activity.activity_type == "row":
                series = extract_distance_time_series(fit_path)
                if series:
                    # Distance PRs: best time to cover each distance
                    rowing_efforts["rowing_500m_time"] = calculate_best_effort_time(series, 500)
                    rowing_efforts["rowing_1k_time"] = calculate_best_effort_time(series, 1000)
                    rowing_efforts["rowing_2k_time"] = calculate_best_effort_time(series, 2000)
                    rowing_efforts["rowing_5k_time"] = calculate_best_effort_time(series, 5000)
                    rowing_efforts["rowing_10k_time"] = calculate_best_effort_time(series, 10000)
                    # Time PRs: best distance covered in each duration
                    rowing_efforts["rowing_1min_distance"] = calculate_best_effort_distance(series, 60)
                    rowing_efforts["rowing_4min_distance"] = calculate_best_effort_distance(series, 240)
                    rowing_efforts["rowing_10min_distance"] = calculate_best_effort_distance(series, 600)
                    rowing_efforts["rowing_20min_distance"] = calculate_best_effort_distance(series, 1200)
                    rowing_efforts["rowing_30min_distance"] = calculate_best_effort_distance(series, 1800)
                    rowing_efforts["rowing_60min_distance"] = calculate_best_effort_distance(series, 3600)

        # Store activity metrics
        metrics = ActivityMetrics(
            activity_id=activity.id,
            tss=tss,
            tss_method=method.value,
            intensity_factor=intensity_factor,
            efficiency_factor=ef,
            variability_index=vi,
            peak_power_5s=peak_powers.get("peak_power_5s"),
            peak_power_1min=peak_powers.get("peak_power_1min"),
            peak_power_5min=peak_powers.get("peak_power_5min"),
            peak_power_20min=peak_powers.get("peak_power_20min"),
            peak_power_4min=peak_powers.get("peak_power_4min"),
            peak_power_30min=peak_powers.get("peak_power_30min"),
            peak_power_60min=peak_powers.get("peak_power_60min"),
            rowing_500m_time=rowing_efforts.get("rowing_500m_time"),
            rowing_1k_time=rowing_efforts.get("rowing_1k_time"),
            rowing_2k_time=rowing_efforts.get("rowing_2k_time"),
            rowing_5k_time=rowing_efforts.get("rowing_5k_time"),
            rowing_10k_time=rowing_efforts.get("rowing_10k_time"),
            rowing_1min_distance=rowing_efforts.get("rowing_1min_distance"),
            rowing_4min_distance=rowing_efforts.get("rowing_4min_distance"),
            rowing_10min_distance=rowing_efforts.get("rowing_10min_distance"),
            rowing_20min_distance=rowing_efforts.get("rowing_20min_distance"),
            rowing_30min_distance=rowing_efforts.get("rowing_30min_distance"),
            rowing_60min_distance=rowing_efforts.get("rowing_60min_distance"),
        )
        repo.insert_activity_metrics(metrics)

        yield {
            "event": "activity",
            "data": json.dumps({
                "activity_id": activity.id,
                "activity_type": activity.activity_type,
                "date": activity.start_time.date().isoformat() if activity.start_time else None,
                "progress": i,
                "total": total_activities,
                "phase": "activities",
            }),
        }
        await asyncio.sleep(0)

    # Phase 2: Calculate daily training load metrics
    if daily_tss:
        metrics_list = calculate_training_load(daily_tss)

        for i, day_metrics in enumerate(metrics_list, 1):
            repo.upsert_daily_metrics(day_metrics)

            yield {
                "event": "daily",
                "data": json.dumps({
                    "date": day_metrics.date.isoformat(),
                    "progress": i,
                    "total": len(metrics_list),
                    "phase": "daily",
                }),
            }
            await asyncio.sleep(0)

    # Mark profile as clean
    repo.set_metrics_dirty(False)

    yield {
        "event": "complete",
        "data": json.dumps({
            "activities_processed": total_activities,
            "days_processed": total_days,
        }),
    }
    await asyncio.sleep(0)


@router.get("/recalculate/stream")
async def recalculate_stream(
    repo: Repository = Depends(get_repo),
):
    """Stream metrics recalculation progress via SSE."""
    return EventSourceResponse(recalculate_generator(repo))
