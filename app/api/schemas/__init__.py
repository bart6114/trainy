"""API schemas package."""

from .common import PaginatedResponse, ErrorResponse, SuccessResponse
from .activities import (
    ActivityResponse,
    ActivityWithMetricsResponse,
    ActivityListResponse,
)
from .metrics import (
    CurrentMetricsResponse,
    DailyMetricsResponse,
    WeeklyTSSResponse,
)
from .profile import ProfileResponse, ProfileUpdateRequest, MaxHRDetectionResponse
from .planned_workouts import (
    PlannedWorkoutResponse,
    GenerateWorkoutsRequest,
    GeneratedWorkoutsResponse,
    UpcomingWorkoutsResponse,
    DateWorkoutsResponse,
)
from .calendar import CalendarMonthResponse, CalendarDateResponse

__all__ = [
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    "ActivityResponse",
    "ActivityWithMetricsResponse",
    "ActivityListResponse",
    "CurrentMetricsResponse",
    "DailyMetricsResponse",
    "WeeklyTSSResponse",
    "ProfileResponse",
    "ProfileUpdateRequest",
    "MaxHRDetectionResponse",
    "PlannedWorkoutResponse",
    "GenerateWorkoutsRequest",
    "GeneratedWorkoutsResponse",
    "UpcomingWorkoutsResponse",
    "DateWorkoutsResponse",
    "CalendarMonthResponse",
    "CalendarDateResponse",
]
