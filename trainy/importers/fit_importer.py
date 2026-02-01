"""FIT file importer for RunGap exports."""

import gzip
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fitparse import FitFile

from ..database.models import Activity


def calculate_peak_power(power_samples: list[float], window_seconds: int, sample_interval: int = 1) -> Optional[float]:
    """Calculate peak (best) average power over a rolling window.

    Args:
        power_samples: List of power values
        window_seconds: Rolling average window size in seconds
        sample_interval: Seconds between samples (default 1, C2 ergs use 3)

    Returns:
        Peak average power in watts, or None if insufficient data
    """
    # Convert window from seconds to number of samples
    window_samples = window_seconds // sample_interval

    if not power_samples or len(power_samples) < window_samples:
        return None

    max_avg = 0.0
    for i in range(len(power_samples) - window_samples + 1):
        window = power_samples[i:i + window_samples]
        avg = sum(window) / window_samples
        if avg > max_avg:
            max_avg = avg

    return round(max_avg, 1) if max_avg > 0 else None


def calculate_all_peak_powers(power_samples: list[float], include_rowing: bool = False, sample_interval: int = 1) -> dict[str, Optional[float]]:
    """Calculate peak powers for all standard durations.

    Args:
        power_samples: List of power values
        include_rowing: Whether to include rowing-specific durations (4min, 30min, 60min)
        sample_interval: Seconds between samples (default 1, C2 ergs use 3)

    Returns:
        Dictionary with peak powers for standard and optionally rowing durations
    """
    peaks = {
        "peak_power_5s": calculate_peak_power(power_samples, 5, sample_interval),
        "peak_power_1min": calculate_peak_power(power_samples, 60, sample_interval),
        "peak_power_5min": calculate_peak_power(power_samples, 300, sample_interval),
        "peak_power_20min": calculate_peak_power(power_samples, 1200, sample_interval),
    }

    if include_rowing:
        peaks.update({
            "peak_power_4min": calculate_peak_power(power_samples, 240, sample_interval),
            "peak_power_30min": calculate_peak_power(power_samples, 1800, sample_interval),
            "peak_power_60min": calculate_peak_power(power_samples, 3600, sample_interval),
        })

    return peaks


def calculate_normalized_power(power_samples: list[float], window_seconds: int = 30) -> Optional[float]:
    """Calculate Normalized Power from power samples.

    NP algorithm:
    1. Calculate 30-second rolling average of power
    2. Raise each rolling average to the 4th power
    3. Take the average of those values
    4. Take the 4th root

    Args:
        power_samples: List of power values (assumed 1-second samples)
        window_seconds: Rolling average window size (default 30s)

    Returns:
        Normalized power in watts, or None if insufficient data
    """
    if not power_samples or len(power_samples) < window_seconds:
        return None

    # Calculate 30-second rolling averages
    rolling_avgs = []
    for i in range(len(power_samples) - window_seconds + 1):
        window = power_samples[i:i + window_seconds]
        avg = sum(window) / window_seconds
        rolling_avgs.append(avg)

    if not rolling_avgs:
        return None

    # Raise to 4th power, average, then 4th root
    fourth_powers = [p ** 4 for p in rolling_avgs]
    np_value = (sum(fourth_powers) / len(fourth_powers)) ** 0.25

    return round(np_value, 1)


# Mapping of sport types from FIT files to our activity types
SPORT_TYPE_MAP = {
    "running": "run",
    "cycling": "cycle",
    "swimming": "swim",
    "walking": "walk",
    "hiking": "hike",
    "strength_training": "strength",
    "cardio_training": "cardio",
    "generic": "other",
    "e_biking": "cycle",
    "indoor_cycling": "cycle",
    "virtual_ride": "cycle",
    "indoor_running": "run",
    "treadmill_running": "run",
    "trail_running": "run",
    "open_water_swimming": "swim",
    "pool_swimming": "swim",
    "lap_swimming": "swim",
    "yoga": "yoga",
    "rowing": "row",
    "indoor_rowing": "row",
    "elliptical": "cardio",
    "stair_stepper": "cardio",
    "transition": "other",
    "multisport": "other",
    # Winter sports
    "cross_country_skiing": "xcski",
    "alpine_skiing": "ski",
    "backcountry_skiing": "ski",
    "snowboarding": "snowboard",
    # Skating
    "inline_skating": "skate",
    "ice_skating": "skate",
    # Other sports
    "tennis": "tennis",
    "golf": "golf",
    "stand_up_paddleboarding": "sup",
    "surfing": "surf",
    "kitesurfing": "kitesurf",
    "windsurfing": "windsurf",
    "wakeboarding": "wakeboard",
    "rock_climbing": "climb",
    "mountaineering": "climb",
    "horseback_riding": "other",
    "driving": "other",
    "fishing": "other",
    "hunting": "other",
    "paddling": "paddle",
    "kayaking": "paddle",
    "sailing": "sail",
    "fitness_equipment": "cardio",
    "training": "cardio",
    "floor_climbing": "cardio",
}

# Source detection from filename patterns
SOURCE_PATTERNS = {
    r"_sa_": "strava",
    r"_gc_": "garmin",
    r"_zw_": "zwift",
    r"_pf_": "pebble",
    r"_fb_": "fitbit",
}


def detect_source(filename: str) -> Optional[str]:
    """Detect activity source from filename pattern."""
    for pattern, source in SOURCE_PATTERNS.items():
        if re.search(pattern, filename):
            return source
    return None


def parse_fit_file(path: Path, include_raw_data: bool = False) -> Optional[Activity]:
    """Parse a FIT file and return an Activity model.

    Args:
        path: Path to the FIT file
        include_raw_data: Whether to include compressed raw FIT data

    Returns:
        Activity model or None if parsing fails
    """
    try:
        fit = FitFile(str(path))
        fit_bytes = path.read_bytes()
        file_hash = hashlib.sha256(fit_bytes).hexdigest()

        # Get session message (summary data)
        session_data = None
        for record in fit.get_messages("session"):
            session_data = {field.name: field.value for field in record.fields}
            break

        if not session_data:
            # Try to get data from activity or record messages
            for record in fit.get_messages("activity"):
                session_data = {field.name: field.value for field in record.fields}
                break

        if not session_data:
            return None

        # Extract start time
        start_time = session_data.get("start_time") or session_data.get("timestamp")
        if not start_time:
            # Try to get from first record
            for record in fit.get_messages("record"):
                ts = None
                for field in record.fields:
                    if field.name == "timestamp":
                        ts = field.value
                        break
                if ts:
                    start_time = ts
                    break

        if not start_time:
            return None

        # Ensure timezone-aware datetime
        if isinstance(start_time, datetime):
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
        else:
            return None

        # Determine activity type - check sub_sport first for more specific classification
        sport = session_data.get("sport", "generic")
        sub_sport = session_data.get("sub_sport")

        activity_type = "other"
        if isinstance(sub_sport, str):
            activity_type = SPORT_TYPE_MAP.get(sub_sport.lower(), "other")
        if activity_type == "other" and isinstance(sport, str):
            activity_type = SPORT_TYPE_MAP.get(sport.lower(), "other")

        # Calculate end time
        duration = session_data.get("total_elapsed_time") or session_data.get("total_timer_time", 0)
        if duration:
            end_time = start_time.replace() + __import__("datetime").timedelta(seconds=duration)
        else:
            end_time = None

        # Extract normalized power for cycling activities only
        is_cycling = activity_type == "cycle"
        normalized_power = None
        power_samples = []

        if is_cycling:
            # First check if NP is in the session data
            normalized_power = session_data.get("normalized_power")

            # If not, calculate from power samples
            if not normalized_power and session_data.get("avg_power"):
                # Need to read power samples from records
                fit_for_records = FitFile(str(path))
                for record in fit_for_records.get_messages("record"):
                    for field in record.fields:
                        if field.name == "power" and field.value is not None:
                            power_samples.append(field.value)
                            break

                if power_samples:
                    normalized_power = calculate_normalized_power(power_samples)

        # Build raw data for storage if requested
        raw_fit_data = None
        if include_raw_data:
            raw_data = {
                "session": session_data,
                "laps": [],
                "records": [],
            }

            # Collect lap data
            for lap in fit.get_messages("lap"):
                lap_data = {field.name: _serialize_value(field.value) for field in lap.fields}
                raw_data["laps"].append(lap_data)

            # Collect record data (sample every 5th record to reduce size)
            record_count = 0
            for record in fit.get_messages("record"):
                record_count += 1
                if record_count % 5 == 0:  # Sample every 5th record
                    record_data = {field.name: _serialize_value(field.value) for field in record.fields}
                    raw_data["records"].append(record_data)

            # Compress the JSON data
            json_str = json.dumps(raw_data, default=str)
            raw_fit_data = gzip.compress(json_str.encode("utf-8"))

        return Activity(
            fit_file_hash=file_hash,
            fit_file_path=str(path),
            start_time=start_time,
            end_time=end_time,
            activity_type=activity_type,
            source=detect_source(path.name),
            duration_seconds=duration or 0,
            distance_meters=session_data.get("total_distance"),
            avg_speed_mps=session_data.get("avg_speed") or session_data.get("enhanced_avg_speed"),
            max_speed_mps=session_data.get("max_speed") or session_data.get("enhanced_max_speed"),
            total_ascent_m=session_data.get("total_ascent"),
            total_descent_m=session_data.get("total_descent"),
            avg_hr=session_data.get("avg_heart_rate"),
            max_hr=session_data.get("max_heart_rate"),
            avg_power=session_data.get("avg_power"),
            max_power=session_data.get("max_power"),
            normalized_power=normalized_power,
            avg_cadence=session_data.get("avg_cadence") or session_data.get("avg_running_cadence"),
            calories=session_data.get("total_calories"),
            title=_generate_title(activity_type, start_time, session_data),
            raw_fit_data=raw_fit_data,
        )

    except Exception as e:
        print(f"Error parsing {path}: {e}")
        return None


def _serialize_value(value):
    """Serialize a value for JSON storage."""
    if isinstance(value, datetime):
        return value.isoformat()
    elif hasattr(value, "__dict__"):
        return str(value)
    return value


def _generate_title(activity_type: str, start_time: datetime, session_data: dict) -> str:
    """Generate a title for the activity."""
    time_of_day = "Morning" if start_time.hour < 12 else "Afternoon" if start_time.hour < 17 else "Evening"
    type_names = {
        "run": "Run",
        "cycle": "Ride",
        "swim": "Swim",
        "walk": "Walk",
        "hike": "Hike",
        "strength": "Strength",
        "cardio": "Cardio",
        "yoga": "Yoga",
        "row": "Row",
        "ski": "Ski",
        "xcski": "XC Ski",
        "snowboard": "Snowboard",
        "skate": "Skate",
        "tennis": "Tennis",
        "golf": "Golf",
        "sup": "SUP",
        "surf": "Surf",
        "kitesurf": "Kitesurf",
        "windsurf": "Windsurf",
        "wakeboard": "Wakeboard",
        "climb": "Climb",
        "paddle": "Paddle",
        "sail": "Sail",
        "other": "Activity",
    }
    type_name = type_names.get(activity_type, "Activity")
    return f"{time_of_day} {type_name}"


def extract_distance_time_series(path: Path) -> list[tuple[float, float]]:
    """Extract distance/time series from a FIT file.

    Args:
        path: Path to the FIT file

    Returns:
        List of (cumulative_distance_meters, elapsed_seconds) tuples
    """
    if not path.exists():
        return []

    try:
        fit = FitFile(str(path))
        series = []
        start_time = None

        for record in fit.get_messages("record"):
            fields = {f.name: f.value for f in record.fields}
            if "distance" in fields and "timestamp" in fields:
                distance = fields["distance"]
                timestamp = fields["timestamp"]
                if distance is not None and timestamp is not None:
                    if start_time is None:
                        start_time = timestamp
                    elapsed = (timestamp - start_time).total_seconds()
                    series.append((distance, elapsed))

        return series
    except Exception:
        return []


def calculate_best_effort_time(distance_time_series: list[tuple[float, float]], target_distance: float, tolerance: float = 0.01) -> Optional[float]:
    """Find the best (fastest) time to cover a target distance using sliding window.

    Args:
        distance_time_series: List of (cumulative_distance, elapsed_seconds) tuples
        target_distance: Target distance in meters
        tolerance: Fraction of target distance to allow as shortfall (default 1%)

    Returns:
        Best time in seconds to cover the target distance, or None if not possible
    """
    if not distance_time_series:
        return None

    first_distance = distance_time_series[0][0]
    max_distance = distance_time_series[-1][0]
    total_covered = max_distance - first_distance
    min_required = target_distance * (1 - tolerance)

    # Not enough distance covered
    if total_covered < min_required:
        return None

    # If the whole activity is within tolerance of target, return total time
    # (handles test pieces that are exactly the target distance)
    if total_covered < target_distance and total_covered >= min_required:
        total_time = distance_time_series[-1][1] - distance_time_series[0][1]
        return round(total_time, 1)

    # Otherwise use sliding window to find best effort
    effective_target = target_distance

    best_time = None
    end_idx = 0

    for start_idx, (start_dist, start_time) in enumerate(distance_time_series):
        # Find the first point where distance >= start_dist + effective_target
        while end_idx < len(distance_time_series):
            end_dist, end_time = distance_time_series[end_idx]
            if end_dist >= start_dist + effective_target:
                # Interpolate for more accurate time
                if end_idx > 0:
                    prev_dist, prev_time = distance_time_series[end_idx - 1]
                    if end_dist > prev_dist:
                        # Linear interpolation to find exact time at target distance
                        target_dist = start_dist + effective_target
                        fraction = (target_dist - prev_dist) / (end_dist - prev_dist)
                        interpolated_time = prev_time + fraction * (end_time - prev_time)
                        elapsed = interpolated_time - start_time
                    else:
                        elapsed = end_time - start_time
                else:
                    elapsed = end_time - start_time

                if best_time is None or elapsed < best_time:
                    best_time = elapsed
                break
            end_idx += 1

        # Reset end_idx to search from current position (optimization)
        if end_idx > start_idx:
            end_idx = start_idx + 1

    return round(best_time, 1) if best_time is not None else None


def calculate_best_effort_distance(distance_time_series: list[tuple[float, float]], target_seconds: float, tolerance: float = 0.01) -> Optional[float]:
    """Find the best (longest) distance covered in a target time using sliding window.

    Args:
        distance_time_series: List of (cumulative_distance, elapsed_seconds) tuples
        target_seconds: Target time in seconds
        tolerance: Fraction of target time to allow as shortfall (default 1%)

    Returns:
        Best distance in meters covered in the target time, or None if not possible
    """
    if not distance_time_series:
        return None

    first_time = distance_time_series[0][1]
    max_time = distance_time_series[-1][1]
    total_duration = max_time - first_time
    min_required = target_seconds * (1 - tolerance)

    # Not enough duration
    if total_duration < min_required:
        return None

    # If the whole activity is within tolerance of target, return total distance
    if total_duration < target_seconds and total_duration >= min_required:
        total_distance = distance_time_series[-1][0] - distance_time_series[0][0]
        return round(total_distance, 1)

    # Otherwise use sliding window to find best effort
    best_distance = None
    end_idx = 0

    for start_idx, (start_dist, start_time) in enumerate(distance_time_series):
        # Find the first point where time >= start_time + target_seconds
        while end_idx < len(distance_time_series):
            end_dist, end_time = distance_time_series[end_idx]
            if end_time >= start_time + target_seconds:
                # Interpolate for more accurate distance
                if end_idx > 0:
                    prev_dist, prev_time = distance_time_series[end_idx - 1]
                    if end_time > prev_time:
                        # Linear interpolation to find exact distance at target time
                        target_time = start_time + target_seconds
                        fraction = (target_time - prev_time) / (end_time - prev_time)
                        interpolated_dist = prev_dist + fraction * (end_dist - prev_dist)
                        distance_covered = interpolated_dist - start_dist
                    else:
                        distance_covered = end_dist - start_dist
                else:
                    distance_covered = end_dist - start_dist

                if best_distance is None or distance_covered > best_distance:
                    best_distance = distance_covered
                break
            end_idx += 1

        # Reset end_idx to search from current position
        if end_idx > start_idx:
            end_idx = start_idx + 1

    return round(best_distance, 1) if best_distance is not None else None


def extract_power_samples_from_fit(path: Path) -> tuple[list[float], int]:
    """Extract power samples from a FIT file with sample interval detection.

    Args:
        path: Path to the FIT file

    Returns:
        Tuple of (power_samples, sample_interval_seconds)
        sample_interval is 1 for most devices, 3 for Concept2 ergs
    """
    if not path.exists():
        return [], 1

    try:
        fit = FitFile(str(path))
        power_samples = []
        timestamps = []

        for record in fit.get_messages("record"):
            fields = {f.name: f.value for f in record.fields}
            if "power" in fields and fields["power"] is not None:
                power_samples.append(fields["power"])
                if "timestamp" in fields:
                    timestamps.append(fields["timestamp"])

        # Detect sample interval from first two timestamps
        sample_interval = 1
        if len(timestamps) >= 2:
            diff = (timestamps[1] - timestamps[0]).total_seconds()
            sample_interval = max(1, int(round(diff)))

        return power_samples, sample_interval
    except Exception:
        return [], 1


class FitImporter:
    """Batch importer for FIT files from RunGap."""

    def __init__(self, rungap_path: Path):
        self.rungap_path = rungap_path

    def get_fit_files(self) -> list[Path]:
        """Get all FIT files in the RunGap export directory."""
        if not self.rungap_path.exists():
            return []
        return sorted(self.rungap_path.glob("*.fit"))

    def count_files(self) -> int:
        """Count FIT files available for import."""
        return len(self.get_fit_files())
