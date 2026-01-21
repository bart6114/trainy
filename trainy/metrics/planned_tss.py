"""TSS calculation for planned workouts."""

from typing import Optional

from ..database.models import UserProfile


# HR Zone to Intensity Factor mapping
HR_ZONE_IF = {
    1: 0.60,
    2: 0.70,
    3: 0.85,
    4: 0.95,
    5: 1.05,
}

# Workout type to Intensity Factor mapping (fallback)
WORKOUT_TYPE_IF = {
    "easy": 0.60,
    "recovery": 0.60,
    "long": 0.70,
    "tempo": 0.85,
    "intervals": 0.95,
    "rest": 0.0,
}

# Default IF for unknown workout types
DEFAULT_IF = 0.70


def calculate_planned_tss(
    duration_s: float,
    activity_type: str,
    workout_type: Optional[str] = None,
    target_hr_zone: Optional[int] = None,
    target_pace_minkm: Optional[float] = None,
    profile: Optional[UserProfile] = None,
) -> tuple[float, float]:
    """Calculate estimated TSS for a planned workout.

    Uses the standard TSS formula: TSS = duration_hours × IF² × 100

    Intensity Factor (IF) is estimated using this priority:
    1. Pace-based (if target_pace_minkm + profile threshold available for run/swim)
    2. HR zone-based (if target_hr_zone provided)
    3. Workout type-based (fallback)

    Args:
        duration_s: Planned workout duration in seconds
        activity_type: Type of activity (run, cycle, swim, strength, rest)
        workout_type: Type of workout (easy, tempo, intervals, long, recovery, rest)
        target_hr_zone: Target HR zone (1-5)
        target_pace_minkm: Target pace in min/km
        profile: User profile with threshold values

    Returns:
        Tuple of (tss, intensity_factor)
    """
    if duration_s <= 0:
        return 0.0, 0.0

    if activity_type == "rest" or workout_type == "rest":
        return 0.0, 0.0

    # Try pace-based IF first (most accurate for running/swimming)
    intensity_factor = _estimate_if_from_pace(
        activity_type, target_pace_minkm, profile
    )

    # Fall back to HR zone if no pace-based IF
    if intensity_factor is None and target_hr_zone is not None:
        intensity_factor = HR_ZONE_IF.get(target_hr_zone, DEFAULT_IF)

    # Fall back to workout type
    if intensity_factor is None and workout_type is not None:
        intensity_factor = WORKOUT_TYPE_IF.get(workout_type, DEFAULT_IF)

    # Final fallback
    if intensity_factor is None:
        intensity_factor = DEFAULT_IF

    # Calculate TSS: duration_hours × IF² × 100
    duration_hours = duration_s / 3600
    tss = duration_hours * intensity_factor * intensity_factor * 100

    return round(tss, 1), round(intensity_factor, 3)


def _estimate_if_from_pace(
    activity_type: str,
    target_pace_minkm: Optional[float],
    profile: Optional[UserProfile],
) -> Optional[float]:
    """Estimate IF from target pace compared to threshold pace.

    IF = threshold_pace / target_pace
    (faster target = higher IF)

    Returns None if insufficient data.
    """
    if target_pace_minkm is None or target_pace_minkm <= 0:
        return None

    if profile is None:
        return None

    if activity_type == "run":
        threshold_pace = profile.threshold_pace_minkm
        if threshold_pace <= 0:
            return None
        # Faster pace = higher IF
        intensity_factor = threshold_pace / target_pace_minkm
        # Cap at reasonable values
        return min(max(intensity_factor, 0.5), 1.5)

    if activity_type == "swim":
        # For swimming, target_pace_minkm is actually min/100m
        threshold_pace = profile.swim_threshold_pace
        if threshold_pace <= 0:
            return None
        intensity_factor = threshold_pace / target_pace_minkm
        return min(max(intensity_factor, 0.5), 1.5)

    return None
