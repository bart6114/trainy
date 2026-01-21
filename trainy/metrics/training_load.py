"""Training load calculations (CTL, ATL, TSB, ACWR, Monotony, Strain)."""

import math
from datetime import date, timedelta
from enum import Enum
from statistics import mean, stdev
from typing import Optional

from ..database.models import DailyMetrics

# EWMA decay factors using true exponential formula: 1 - e^(-1/k)
# Reference: TrainingPeaks Performance Manager (Coggan/Allen)
# https://www.trainingpeaks.com/learn/articles/the-science-of-the-performance-manager/
CTL_DECAY = 1 - math.exp(-1 / 42)  # ≈ 0.02353 (42-day time constant)
ATL_DECAY = 1 - math.exp(-1 / 7)  # ≈ 0.13314 (7-day time constant)


class ACWRZone(Enum):
    """ACWR risk zones for injury prevention."""

    UNDERTRAINED = "undertrained"  # < 0.8
    OPTIMAL = "optimal"  # 0.8 - 1.3 (sweet spot)
    CAUTION = "caution"  # 1.3 - 1.5
    DANGER = "danger"  # > 1.5


def calculate_training_load(
    daily_tss: list[tuple[date, float]],
    start_ctl: float = 0.0,
    start_atl: float = 0.0,
) -> list[DailyMetrics]:
    """Calculate CTL, ATL, TSB for a series of daily TSS values.

    Uses Exponentially Weighted Moving Average (EWMA) with true exponential decay:
    - CTL (Chronic Training Load): 42-day time constant, decay = 1 - e^(-1/42)
    - ATL (Acute Training Load): 7-day time constant, decay = 1 - e^(-1/7)
    - TSB (Training Stress Balance): CTL - ATL

    Formula: value_today = value_yesterday + (TSS - value_yesterday) * decay

    Args:
        daily_tss: List of (date, tss) tuples sorted by date
        start_ctl: Initial CTL value (default 0)
        start_atl: Initial ATL value (default 0)

    Returns:
        List of DailyMetrics with CTL, ATL, TSB filled in
    """
    if not daily_tss:
        return []

    # Sort by date
    daily_tss = sorted(daily_tss, key=lambda x: x[0])

    # Fill in gaps with zero TSS days
    filled_data = _fill_date_gaps(daily_tss)

    ctl = start_ctl
    atl = start_atl
    results = []

    # Keep track of TSS for rolling sums
    tss_history: list[float] = []

    for day, tss in filled_data:
        # EWMA update using true exponential decay
        ctl = ctl + (tss - ctl) * CTL_DECAY
        atl = atl + (tss - atl) * ATL_DECAY
        tsb = ctl - atl

        # Add to history for rolling sums
        tss_history.append(tss)

        # Calculate rolling sums
        tss_7day = sum(tss_history[-7:])
        tss_30day = sum(tss_history[-30:])
        tss_90day = sum(tss_history[-90:])

        # Calculate ACWR
        acwr_value, _ = calculate_acwr(atl, ctl)

        # Calculate Monotony and Strain (need 7 days of data)
        monotony, strain_val = calculate_monotony_strain(tss_history)

        results.append(
            DailyMetrics(
                date=day,
                total_tss=tss,
                ctl=round(ctl, 1),
                atl=round(atl, 1),
                tsb=round(tsb, 1),
                tss_7day=round(tss_7day, 1),
                tss_30day=round(tss_30day, 1),
                tss_90day=round(tss_90day, 1),
                acwr=acwr_value,
                monotony=monotony,
                strain=strain_val,
            )
        )

    return results


def _fill_date_gaps(daily_tss: list[tuple[date, float]]) -> list[tuple[date, float]]:
    """Fill gaps in the date series with zero TSS values."""
    if not daily_tss:
        return []

    result = []
    sorted_data = sorted(daily_tss, key=lambda x: x[0])

    # Create a dict for quick lookup
    tss_by_date = {d: t for d, t in sorted_data}

    # Fill from first to last date
    current = sorted_data[0][0]
    end = sorted_data[-1][0]

    while current <= end:
        tss = tss_by_date.get(current, 0.0)
        result.append((current, tss))
        current += timedelta(days=1)

    return result


def get_form_status(tsb: float) -> tuple[str, str]:
    """Get form status description based on TSB.

    Returns:
        Tuple of (status_name, status_color)
    """
    if tsb > 25:
        return "Transition", "yellow"
    elif tsb > 5:
        return "Fresh", "green"
    elif tsb > -10:
        return "Neutral", "blue"
    elif tsb > -30:
        return "Tired", "orange"
    else:
        return "Exhausted", "red"


def get_ramp_rate(tss_history: list[float], weeks: int = 4) -> Optional[float]:
    """Calculate weekly TSS ramp rate.

    Returns the average week-over-week percentage change in TSS.
    """
    if len(tss_history) < weeks * 7:
        return None

    weekly_totals = []
    for i in range(weeks):
        start_idx = -(i + 1) * 7
        end_idx = -i * 7 if i > 0 else None
        week_tss = sum(tss_history[start_idx:end_idx])
        weekly_totals.append(week_tss)

    # Calculate average week-over-week change
    changes = []
    for i in range(len(weekly_totals) - 1):
        if weekly_totals[i + 1] > 0:
            change = (weekly_totals[i] - weekly_totals[i + 1]) / weekly_totals[i + 1] * 100
            changes.append(change)

    if changes:
        return round(sum(changes) / len(changes), 1)
    return None


def check_overtraining_risk(atl: float, ctl: float, tsb: float) -> list[str]:
    """Check for potential overtraining indicators.

    Returns list of warning messages.
    """
    warnings = []

    # Very negative TSB
    if tsb < -30:
        warnings.append("High fatigue: TSB below -30. Consider rest.")

    # ATL much higher than CTL
    if ctl > 0 and atl > ctl * 1.5:
        warnings.append("Acute load significantly exceeds chronic load.")

    # Extended period of high stress
    if tsb < -20:
        warnings.append("Extended stress period. Monitor recovery.")

    return warnings


def calculate_acwr(atl: float, ctl: float) -> tuple[Optional[float], ACWRZone]:
    """Calculate Acute:Chronic Workload Ratio.

    ACWR is a key injury risk predictor used in sports science.
    Formula: ACWR = ATL / CTL

    Risk zones:
    - <0.8: Undertrained (detraining risk)
    - 0.8-1.3: Optimal (sweet spot)
    - 1.3-1.5: Caution (elevated injury risk)
    - >1.5: Danger (high injury risk)

    Args:
        atl: Acute Training Load (7-day EWMA)
        ctl: Chronic Training Load (42-day EWMA)

    Returns:
        Tuple of (acwr_value, risk_zone)
    """
    if ctl <= 0:
        return None, ACWRZone.UNDERTRAINED

    acwr = atl / ctl

    if acwr < 0.8:
        zone = ACWRZone.UNDERTRAINED
    elif acwr <= 1.3:
        zone = ACWRZone.OPTIMAL
    elif acwr <= 1.5:
        zone = ACWRZone.CAUTION
    else:
        zone = ACWRZone.DANGER

    return round(acwr, 2), zone


def calculate_monotony_strain(tss_7day: list[float]) -> tuple[Optional[float], Optional[float]]:
    """Calculate training Monotony and Strain (Foster method).

    Monotony measures how similar training is day-to-day.
    Strain combines weekly load with monotony for overtraining risk.

    Formulas:
    - Monotony = mean(7-day TSS) / stdev(7-day TSS)
    - Strain = 7-day total TSS × Monotony

    Risk thresholds:
    - Monotony > 2.0: Training too repetitive, higher injury risk
    - Strain > 6000: Very high load, monitor recovery closely

    Args:
        tss_7day: List of last 7 days of TSS values

    Returns:
        Tuple of (monotony, strain)
    """
    if len(tss_7day) < 7:
        return None, None

    # Use the last 7 days
    last_7 = tss_7day[-7:]

    try:
        avg_tss = mean(last_7)
        std_tss = stdev(last_7)

        if std_tss == 0:
            # All days identical = infinite monotony, cap at high value
            monotony = 10.0
        else:
            monotony = avg_tss / std_tss

        total_tss = sum(last_7)
        strain = total_tss * monotony

        return round(monotony, 2), round(strain, 0)
    except Exception:
        return None, None


def get_monotony_status(monotony: Optional[float]) -> tuple[str, str]:
    """Get monotony status description.

    Returns:
        Tuple of (status_name, status_color)
    """
    if monotony is None:
        return "Unknown", "gray"
    elif monotony > 2.0:
        return "High Risk", "red"
    elif monotony > 1.5:
        return "Elevated", "orange"
    else:
        return "Good", "green"


def get_strain_status(strain: Optional[float]) -> tuple[str, str]:
    """Get strain status description.

    Returns:
        Tuple of (status_name, status_color)
    """
    if strain is None:
        return "Unknown", "gray"
    elif strain > 6000:
        return "Very High", "red"
    elif strain > 4000:
        return "High", "orange"
    elif strain > 2000:
        return "Moderate", "yellow"
    else:
        return "Low", "green"


def get_acwr_status(acwr: Optional[float]) -> tuple[str, str]:
    """Get ACWR status description.

    Returns:
        Tuple of (status_name, status_color)
    """
    if acwr is None:
        return "Unknown", "gray"
    elif acwr < 0.8:
        return "Undertrained", "yellow"
    elif acwr <= 1.3:
        return "Optimal", "green"
    elif acwr <= 1.5:
        return "Caution", "orange"
    else:
        return "Danger", "red"
