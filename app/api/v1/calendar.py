"""Calendar API endpoints."""

from calendar import monthrange
from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, Path

from trainy.database import Repository
from trainy.database.models import PlannedWorkout
from app.dependencies import get_repo
from app.api.schemas.calendar import (
    CalendarActivity,
    CalendarPlannedWorkout,
    CalendarDay,
    CalendarMonthResponse,
    CalendarDateResponse,
)

router = APIRouter()


def _make_calendar_activity(activity, metrics) -> CalendarActivity:
    """Convert activity and metrics to CalendarActivity."""
    return CalendarActivity(
        id=activity.id,
        activity_type=activity.activity_type,
        title=activity.title,
        duration_seconds=activity.duration_seconds,
        distance_meters=activity.distance_meters,
        tss=metrics.tss if metrics else None,
    )


def _make_calendar_planned_workout(workout: PlannedWorkout) -> CalendarPlannedWorkout:
    """Convert PlannedWorkout to CalendarPlannedWorkout."""
    return CalendarPlannedWorkout(
        id=workout.id,
        activity_type=workout.activity_type,
        workout_type=workout.workout_type,
        title=workout.title,
        description=workout.description,
        target_duration_s=workout.target_duration_s,
        target_tss=workout.target_tss,
        status=workout.status,
        completed_activity_id=workout.completed_activity_id,
    )


# NOTE: /date/{date_str} must come before /{year}/{month} to avoid route conflict
@router.get("/date/{date_str}", response_model=CalendarDateResponse)
async def get_calendar_date(
    date_str: str = Path(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    repo: Repository = Depends(get_repo),
):
    """Get activities and planned workouts for a specific date."""
    target_date = date.fromisoformat(date_str)

    # Get activities
    activities = repo.get_activities_for_date(target_date)
    calendar_activities = []
    total_tss = 0.0

    for activity in activities:
        metrics = repo.get_activity_metrics(activity.id)
        calendar_activities.append(_make_calendar_activity(activity, metrics))
        if metrics and metrics.tss:
            total_tss += metrics.tss

    # Get planned workouts
    planned_workouts = repo.get_planned_workouts_for_date(target_date)
    calendar_workouts = [_make_calendar_planned_workout(w) for w in planned_workouts]

    return CalendarDateResponse(
        date=target_date,
        activities=calendar_activities,
        planned_workouts=calendar_workouts,
        total_tss=total_tss,
    )


@router.get("/{year}/{month}", response_model=CalendarMonthResponse)
async def get_calendar_month(
    year: int = Path(..., ge=2000, le=2100),
    month: int = Path(..., ge=1, le=12),
    repo: Repository = Depends(get_repo),
):
    """Get calendar data for a month."""
    # Get date range for the month
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    # Get all activities for the month
    activities = repo.get_activities_by_date_range(first_day, last_day)

    # Get all planned workouts for the month
    planned_workouts = repo.get_planned_workouts_range(first_day, last_day)

    # Group activities by date
    activities_by_date: dict[date, list[CalendarActivity]] = defaultdict(list)
    for activity in activities:
        activity_date = activity.start_time.date()
        metrics = repo.get_activity_metrics(activity.id)
        activities_by_date[activity_date].append(_make_calendar_activity(activity, metrics))

    # Group planned workouts by date
    workouts_by_date: dict[date, list[CalendarPlannedWorkout]] = defaultdict(list)
    for workout in planned_workouts:
        workouts_by_date[workout.planned_date].append(_make_calendar_planned_workout(workout))

    # Combine all dates that have activities or planned workouts
    all_dates = set(activities_by_date.keys()) | set(workouts_by_date.keys())

    # Build response
    days = []
    for d in sorted(all_dates):
        acts = activities_by_date.get(d, [])
        workouts = workouts_by_date.get(d, [])
        total_tss = sum(a.tss or 0 for a in acts)
        days.append(
            CalendarDay(
                date=d,
                activities=acts,
                planned_workouts=workouts,
                total_tss=total_tss,
                activity_count=len(acts),
            )
        )

    return CalendarMonthResponse(
        year=year,
        month=month,
        days=days,
    )
