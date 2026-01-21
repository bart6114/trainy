"""Profile API endpoints."""

from datetime import date

from fastapi import APIRouter, Depends

from trainy.database import Repository
from app.dependencies import get_repo
from app.api.schemas.profile import (
    ProfileResponse,
    ProfileUpdateRequest,
    MaxHRDetectionResponse,
)

router = APIRouter()


@router.get("", response_model=ProfileResponse)
async def get_profile(
    repo: Repository = Depends(get_repo),
):
    """Get current user profile."""
    profile = repo.get_current_profile()
    return ProfileResponse(
        id=profile.id,
        ftp=profile.ftp,
        lthr=profile.lthr,
        max_hr=profile.max_hr,
        resting_hr=profile.resting_hr,
        threshold_pace_minkm=profile.threshold_pace_minkm,
        swim_threshold_pace=profile.swim_threshold_pace,
        weight_kg=profile.weight_kg,
        effective_from=profile.effective_from,
        metrics_dirty=profile.metrics_dirty,
    )


@router.put("", response_model=ProfileResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    repo: Repository = Depends(get_repo),
):
    """Update user profile."""
    current = repo.get_current_profile()

    # Update only provided fields
    if request.ftp is not None:
        current.ftp = request.ftp
    if request.lthr is not None:
        current.lthr = request.lthr
    if request.max_hr is not None:
        current.max_hr = request.max_hr
    if request.resting_hr is not None:
        current.resting_hr = request.resting_hr
    if request.threshold_pace_minkm is not None:
        current.threshold_pace_minkm = request.threshold_pace_minkm
    if request.swim_threshold_pace is not None:
        current.swim_threshold_pace = request.swim_threshold_pace
    if request.weight_kg is not None:
        current.weight_kg = request.weight_kg

    # Mark metrics as dirty since thresholds changed
    current.metrics_dirty = True

    if current.id:
        repo.update_profile(current)
    else:
        current.id = repo.save_profile(current)

    return ProfileResponse(
        id=current.id,
        ftp=current.ftp,
        lthr=current.lthr,
        max_hr=current.max_hr,
        resting_hr=current.resting_hr,
        threshold_pace_minkm=current.threshold_pace_minkm,
        swim_threshold_pace=current.swim_threshold_pace,
        weight_kg=current.weight_kg,
        effective_from=current.effective_from,
        metrics_dirty=current.metrics_dirty,
    )


@router.post("/detect-max-hr", response_model=MaxHRDetectionResponse)
async def detect_max_hr(
    repo: Repository = Depends(get_repo),
):
    """Auto-detect max HR from recent activities."""
    # Get activities from last 90 days
    activities = repo.get_recent_activities(days=90)

    # Find max HR values
    max_hrs = [a.max_hr for a in activities if a.max_hr and a.max_hr > 100]

    if not max_hrs:
        return MaxHRDetectionResponse(
            detected_max_hr=None,
            sample_count=0,
            confidence="none",
            message="No activities with valid heart rate data found",
        )

    # Use 95th percentile to avoid outliers
    max_hrs.sort(reverse=True)
    idx = max(0, int(len(max_hrs) * 0.05))
    detected = max_hrs[idx]

    # Determine confidence based on sample size
    if len(max_hrs) >= 20:
        confidence = "high"
        message = f"Detected max HR of {detected} bpm from {len(max_hrs)} activities"
    elif len(max_hrs) >= 10:
        confidence = "medium"
        message = f"Detected max HR of {detected} bpm from {len(max_hrs)} activities (moderate confidence)"
    else:
        confidence = "low"
        message = f"Detected max HR of {detected} bpm from only {len(max_hrs)} activities (low confidence)"

    return MaxHRDetectionResponse(
        detected_max_hr=detected,
        sample_count=len(max_hrs),
        confidence=confidence,
        message=message,
    )
