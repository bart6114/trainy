"""Training Stress Score (TSS) calculations."""

from enum import Enum
from typing import Optional

from ..database.models import Activity, UserProfile


class TSSMethod(Enum):
    """Method used to calculate TSS."""

    POWER = "power"
    HEART_RATE = "hr"
    PACE = "pace"
    DURATION = "duration"  # Fallback based on duration only


def calculate_tss(
    activity: Activity,
    profile: UserProfile,
    raw_data: Optional[dict] = None,
) -> tuple[float, TSSMethod, float]:
    """Calculate TSS for an activity based on available data.

    Returns:
        Tuple of (tss, method_used, intensity_factor)
    """
    # Try power-based TSS first (most accurate for cycling)
    if activity.activity_type == "cycle" and activity.avg_power and activity.avg_power > 0:
        tss, if_value = _calculate_power_tss(activity, profile)
        return tss, TSSMethod.POWER, if_value

    # Try heart rate TSS for activities with HR data
    if activity.avg_hr and activity.avg_hr > 0:
        tss, if_value = _calculate_hr_tss(activity, profile)
        return tss, TSSMethod.HEART_RATE, if_value

    # Try pace-based TSS for running/swimming
    if activity.activity_type == "run" and activity.distance_meters and activity.distance_meters > 0:
        tss, if_value = _calculate_run_pace_tss(activity, profile)
        return tss, TSSMethod.PACE, if_value

    if activity.activity_type == "swim" and activity.distance_meters and activity.distance_meters > 0:
        tss, if_value = _calculate_swim_pace_tss(activity, profile)
        return tss, TSSMethod.PACE, if_value

    # Fallback: duration-based estimate
    tss, if_value = _calculate_duration_tss(activity)
    return tss, TSSMethod.DURATION, if_value


def _calculate_power_tss(activity: Activity, profile: UserProfile) -> tuple[float, float]:
    """Calculate power-based TSS for cycling.

    TSS = (duration_s * NP * IF) / (FTP * 3600) * 100
    where IF = NP / FTP

    If normalized power is not available, use average power.
    """
    ftp = profile.ftp
    if ftp <= 0:
        return 0.0, 0.0

    # Use normalized power if available, otherwise average power
    power = activity.normalized_power or activity.avg_power
    if not power or power <= 0:
        return 0.0, 0.0

    intensity_factor = power / ftp
    duration_hours = activity.duration_seconds / 3600

    tss = duration_hours * intensity_factor * intensity_factor * 100

    return round(tss, 1), round(intensity_factor, 3)


def _calculate_hr_tss(activity: Activity, profile: UserProfile) -> tuple[float, float]:
    """Calculate heart rate-based TSS (hrTSS).

    Uses the industry-standard TrainingPeaks formula:
    hrTSS = duration_hours × IF² × 100
    where IF = avg_hr / LTHR

    This matches the power-based TSS formula structure for consistency.
    """
    lthr = profile.lthr

    if lthr <= 0:
        return 0.0, 0.0

    avg_hr = activity.avg_hr
    if not avg_hr or avg_hr <= 0:
        return 0.0, 0.0

    # Intensity factor based on LTHR
    intensity_factor = avg_hr / lthr

    # Calculate hrTSS using IF-squared formula (matches power TSS)
    duration_hours = activity.duration_seconds / 3600
    hr_tss = duration_hours * intensity_factor * intensity_factor * 100

    return round(hr_tss, 1), round(intensity_factor, 3)


def _calculate_run_pace_tss(activity: Activity, profile: UserProfile) -> tuple[float, float]:
    """Calculate running TSS (rTSS) based on pace.

    IF = threshold_pace / actual_pace (faster = higher IF)
    rTSS = (duration_h) * IF^2 * 100
    """
    threshold_pace = profile.threshold_pace_minkm
    if threshold_pace <= 0 or not activity.distance_meters:
        return 0.0, 0.0

    # Calculate actual pace in min/km
    distance_km = activity.distance_meters / 1000
    if distance_km <= 0:
        return 0.0, 0.0

    duration_minutes = activity.duration_seconds / 60
    actual_pace = duration_minutes / distance_km

    if actual_pace <= 0:
        return 0.0, 0.0

    # Faster pace = higher IF (threshold pace is the reference)
    intensity_factor = threshold_pace / actual_pace

    # Cap IF at reasonable values
    intensity_factor = min(intensity_factor, 1.5)

    # Calculate rTSS
    duration_hours = activity.duration_seconds / 3600
    r_tss = duration_hours * intensity_factor * intensity_factor * 100

    return round(r_tss, 1), round(intensity_factor, 3)


def _calculate_swim_pace_tss(activity: Activity, profile: UserProfile) -> tuple[float, float]:
    """Calculate swimming TSS based on pace.

    Similar to running but uses min/100m as pace unit.
    """
    threshold_pace = profile.swim_threshold_pace
    if threshold_pace <= 0 or not activity.distance_meters:
        return 0.0, 0.0

    # Calculate actual pace in min/100m
    distance_100m = activity.distance_meters / 100
    if distance_100m <= 0:
        return 0.0, 0.0

    duration_minutes = activity.duration_seconds / 60
    actual_pace = duration_minutes / distance_100m

    if actual_pace <= 0:
        return 0.0, 0.0

    intensity_factor = threshold_pace / actual_pace
    intensity_factor = min(intensity_factor, 1.5)

    duration_hours = activity.duration_seconds / 3600
    swim_tss = duration_hours * intensity_factor * intensity_factor * 100

    return round(swim_tss, 1), round(intensity_factor, 3)


def _calculate_duration_tss(activity: Activity) -> tuple[float, float]:
    """Fallback TSS estimate based on duration only.

    Assumes moderate intensity (IF = 0.7) for activities without other metrics.
    """
    # Moderate effort assumption
    intensity_factor = 0.7

    # Adjust based on activity type
    activity_intensity = {
        "strength": 0.6,
        "yoga": 0.4,
        "walk": 0.5,
        "cardio": 0.75,
        "hike": 0.65,
        "other": 0.6,
    }

    if activity.activity_type in activity_intensity:
        intensity_factor = activity_intensity[activity.activity_type]

    duration_hours = activity.duration_seconds / 3600
    tss = duration_hours * intensity_factor * intensity_factor * 100

    return round(tss, 1), round(intensity_factor, 3)
