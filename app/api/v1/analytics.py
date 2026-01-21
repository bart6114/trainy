"""Analytics API endpoints."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query

from trainy.database import Repository
from trainy.metrics.critical_power import estimate_ftp_with_fallback
from app.dependencies import get_repo
from app.api.schemas.analytics import PowerCurveResponse, PowerCurvePoint

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
