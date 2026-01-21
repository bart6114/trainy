"""Database models using Pydantic for validation."""

from datetime import datetime, date
from typing import Literal, Optional
from pydantic import BaseModel, Field


class Activity(BaseModel):
    """Activity record parsed from FIT files."""

    id: Optional[int] = None
    fit_file_hash: str
    fit_file_path: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None

    # Classification
    activity_type: str  # 'run', 'cycle', 'swim', 'strength', 'other'
    source: Optional[str] = None  # 'strava', 'garmin', 'zwift'

    # Core metrics (SI units)
    duration_seconds: float
    distance_meters: Optional[float] = None
    avg_speed_mps: Optional[float] = None
    max_speed_mps: Optional[float] = None

    # Elevation
    total_ascent_m: Optional[float] = None
    total_descent_m: Optional[float] = None

    # Heart rate
    avg_hr: Optional[int] = None
    max_hr: Optional[int] = None

    # Power (cycling)
    avg_power: Optional[float] = None
    max_power: Optional[float] = None
    normalized_power: Optional[float] = None

    # Cadence
    avg_cadence: Optional[int] = None

    # Energy
    calories: Optional[int] = None

    # Metadata
    title: Optional[str] = None
    imported_at: Optional[datetime] = None

    # Raw FIT data (gzip-compressed JSON)
    raw_fit_data: Optional[bytes] = None

    # Joined from activity_metrics (not stored in activities table)
    tss: Optional[float] = None


class ActivityMetrics(BaseModel):
    """Computed metrics for an activity."""

    id: Optional[int] = None
    activity_id: int

    tss: Optional[float] = None
    tss_method: Optional[str] = None  # 'power', 'hr', 'pace'
    intensity_factor: Optional[float] = None

    # Efficiency metrics
    efficiency_factor: Optional[float] = None  # Power or speed per HR beat
    variability_index: Optional[float] = None  # NP/AP ratio (cycling only)

    # Power peaks
    peak_power_5s: Optional[float] = None
    peak_power_1min: Optional[float] = None
    peak_power_5min: Optional[float] = None
    peak_power_20min: Optional[float] = None

    calculated_at: Optional[datetime] = None


class DailyMetrics(BaseModel):
    """Daily aggregated training metrics."""

    date: date
    total_tss: float = 0.0
    activity_count: int = 0
    total_duration_s: float = 0.0
    total_distance_m: float = 0.0

    # Training Load (EWMA)
    ctl: Optional[float] = None  # Chronic (42-day)
    atl: Optional[float] = None  # Acute (7-day)
    tsb: Optional[float] = None  # Stress Balance (CTL - ATL)

    # Rolling sums
    tss_7day: Optional[float] = None
    tss_30day: Optional[float] = None
    tss_90day: Optional[float] = None

    # ACWR (Acute:Chronic Workload Ratio)
    acwr: Optional[float] = None  # ATL/CTL ratio for injury risk

    # Monotony & Strain (Foster method)
    monotony: Optional[float] = None  # Training variation indicator
    strain: Optional[float] = None  # Weekly load × monotony


class UserProfile(BaseModel):
    """User profile with threshold values."""

    id: Optional[int] = None
    ftp: int = 200  # Functional Threshold Power (watts)
    lthr: int = 165  # Lactate Threshold HR (bpm)
    max_hr: int = 185  # Max heart rate
    resting_hr: int = 50  # Resting HR
    threshold_pace_minkm: float = 5.0  # Running threshold pace (min/km)
    swim_threshold_pace: float = 2.0  # Swimming threshold (min/100m)
    weight_kg: float = 70.0
    effective_from: date = Field(default_factory=date.today)
    metrics_dirty: bool = True


class PlannedWorkout(BaseModel):
    """Standalone planned workout."""

    id: Optional[int] = None

    planned_date: date
    activity_type: str  # 'run', 'cycle', 'swim', 'strength', 'rest'
    workout_type: Optional[str] = None  # 'easy', 'tempo', 'intervals', 'long'

    title: str
    description: Optional[str] = None
    structured_workout: Optional[str] = None  # JSON for intervals

    # Targets
    target_duration_s: Optional[float] = None
    target_distance_m: Optional[float] = None
    target_tss: Optional[float] = None
    target_calories: Optional[int] = None
    target_hr_zone: Optional[int] = None
    target_pace_minkm: Optional[float] = None

    # Status
    status: str = "planned"  # 'planned', 'completed', 'skipped'
    completed_activity_id: Optional[int] = None

    created_at: Optional[datetime] = None


class WorkoutFeedback(BaseModel):
    """User feedback for a workout."""

    id: Optional[int] = None
    activity_id: Optional[int] = None
    planned_workout_id: Optional[int] = None

    # Subjective ratings (1-10)
    rpe: Optional[int] = None  # Rate of Perceived Exertion
    comfort_level: Optional[int] = None
    energy_level: Optional[int] = None
    motivation: Optional[int] = None

    # Physical state
    sleep_hours: Optional[float] = None
    sleep_quality: Optional[int] = None
    muscle_soreness: Optional[int] = None
    fatigue_level: Optional[int] = None

    # Injury tracking
    has_pain: bool = False
    pain_location: Optional[str] = None
    pain_severity: Optional[int] = None

    # Notes
    notes: Optional[str] = None

    created_at: Optional[datetime] = None


class UserSettings(BaseModel):
    """User settings for wellness tracking features."""

    id: Optional[int] = None

    # Morning check-in toggles
    morning_checkin_enabled: bool = False
    morning_sleep_quality_enabled: bool = False
    morning_sleep_hours_enabled: bool = False
    morning_muscle_soreness_enabled: bool = False
    morning_energy_enabled: bool = False
    morning_mood_enabled: bool = False

    # Post-workout feedback toggles
    post_workout_feedback_enabled: bool = False
    post_workout_rpe_enabled: bool = False
    post_workout_pain_enabled: bool = False
    post_workout_session_feel_enabled: bool = False
    post_workout_notes_enabled: bool = False


class MorningCheckin(BaseModel):
    """Daily morning wellness check-in (not tied to activities)."""

    id: Optional[int] = None
    checkin_date: date

    # Wellness metrics (all 1-10 scale except sleep_hours)
    sleep_quality: Optional[int] = None
    sleep_hours: Optional[float] = None
    muscle_soreness: Optional[int] = None
    energy_level: Optional[int] = None
    mood: Optional[int] = None

    notes: Optional[str] = None
    created_at: Optional[datetime] = None
