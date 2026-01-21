"""Efficiency metrics calculations (EF, VI)."""

from typing import Optional

from ..database.models import Activity


def calculate_efficiency_factor(
    activity: Activity,
    normalized_power: Optional[float] = None,
) -> Optional[float]:
    """Calculate Efficiency Factor (EF).

    EF tracks aerobic fitness improvement over time.
    Higher EF = more power/speed per heartbeat = better aerobic fitness.

    Formulas:
    - Cycling: EF = Normalized_Power / avg_hr
    - Running: EF = speed (m/min) / avg_hr

    Args:
        activity: Activity with HR and power/speed data
        normalized_power: Optional NP override

    Returns:
        Efficiency Factor value, or None if insufficient data
    """
    if not activity.avg_hr or activity.avg_hr <= 0:
        return None

    avg_hr = activity.avg_hr

    if activity.activity_type == "cycle":
        # Use normalized power if available, otherwise average power
        power = normalized_power or activity.normalized_power or activity.avg_power
        if not power or power <= 0:
            return None
        ef = power / avg_hr
        return round(ef, 3)

    elif activity.activity_type == "run":
        # Use speed in meters per minute
        if not activity.avg_speed_mps or activity.avg_speed_mps <= 0:
            return None
        speed_mpm = activity.avg_speed_mps * 60  # m/s to m/min
        ef = speed_mpm / avg_hr
        return round(ef, 3)

    elif activity.activity_type == "swim":
        # Use speed in meters per minute
        if not activity.avg_speed_mps or activity.avg_speed_mps <= 0:
            return None
        speed_mpm = activity.avg_speed_mps * 60
        ef = speed_mpm / avg_hr
        return round(ef, 3)

    return None


def calculate_variability_index(activity: Activity) -> Optional[float]:
    """Calculate Variability Index (VI).

    VI indicates pacing quality and metabolic cost.
    Only applicable to cycling with power data.

    Formula: VI = Normalized_Power / Average_Power

    Interpretation:
    - 1.00-1.05: Very steady (time trial, triathlon)
    - 1.05-1.10: Moderate variation (typical training ride)
    - >1.10: Highly variable (criterium, mountain bike, intervals)

    Args:
        activity: Activity with power data

    Returns:
        Variability Index, or None if insufficient data
    """
    if activity.activity_type != "cycle":
        return None

    np = activity.normalized_power
    avg_power = activity.avg_power

    if not np or not avg_power or np <= 0 or avg_power <= 0:
        return None

    vi = np / avg_power
    return round(vi, 3)


def get_variability_status(vi: Optional[float]) -> tuple[str, str]:
    """Get VI status description.

    Returns:
        Tuple of (status_name, status_color)
    """
    if vi is None:
        return "N/A", "gray"
    elif vi <= 1.05:
        return "Very Steady", "green"
    elif vi <= 1.10:
        return "Moderate", "blue"
    else:
        return "Variable", "orange"


def calculate_intensity_factor_power(
    power: float,
    ftp: float,
) -> Optional[float]:
    """Calculate power-based Intensity Factor.

    Formula: IF = NP / FTP

    Args:
        power: Normalized power (or average if NP unavailable)
        ftp: Functional Threshold Power

    Returns:
        Intensity Factor, or None if invalid inputs
    """
    if ftp <= 0 or power <= 0:
        return None
    return round(power / ftp, 3)
