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

        # Determine activity type
        sport = session_data.get("sport", "generic")
        if isinstance(sport, str):
            activity_type = SPORT_TYPE_MAP.get(sport.lower(), "other")
        else:
            activity_type = "other"

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
