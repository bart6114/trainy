"""Adherence tracking - match actual activities with planned workouts."""

from datetime import date

from .database.models import Activity, PlannedWorkout
from .database.repository import Repository


# Mapping of activity types that should be considered equivalent
ACTIVITY_TYPE_ALIASES = {
    "run": {"run", "running", "trail_running", "treadmill"},
    "cycle": {"cycle", "cycling", "virtual_ride", "indoor_cycling"},
    "swim": {"swim", "swimming", "pool_swim", "open_water_swim"},
    "strength": {"strength", "weight_training", "gym"},
}


def _normalize_activity_type(activity_type: str) -> str:
    """Normalize activity type to a base type."""
    activity_type = activity_type.lower()
    for base_type, aliases in ACTIVITY_TYPE_ALIASES.items():
        if activity_type in aliases:
            return base_type
    return activity_type


def _types_match(planned_type: str, actual_type: str) -> bool:
    """Check if activity types match (allowing for aliases)."""
    return _normalize_activity_type(planned_type) == _normalize_activity_type(actual_type)


def _calculate_match_score(workout: PlannedWorkout, activity: Activity) -> float:
    """Calculate match score between a planned workout and an activity.

    Returns a score between 0 and 1:
    - 0.5 base score if types match (required)
    - +0.25 if duration is within 30% of target
    - +0.25 if distance is within 30% of target (if applicable)
    """
    # Types must match for any score
    if not _types_match(workout.activity_type, activity.activity_type):
        return 0.0

    score = 0.5  # Base score for matching type

    # Check duration match
    if workout.target_duration_s and activity.duration_seconds:
        ratio = activity.duration_seconds / workout.target_duration_s
        if 0.7 <= ratio <= 1.3:  # Within 30%
            score += 0.25

    # Check distance match
    if workout.target_distance_m and activity.distance_meters:
        ratio = activity.distance_meters / workout.target_distance_m
        if 0.7 <= ratio <= 1.3:  # Within 30%
            score += 0.25
    elif not workout.target_distance_m:
        # If no target distance, give full points for duration-based workouts
        score += 0.25

    return score


def _find_best_match(workout: PlannedWorkout, activities: list[Activity]) -> tuple[Activity | None, float]:
    """Find the best matching activity for a planned workout."""
    best_activity = None
    best_score = 0.0

    for activity in activities:
        score = _calculate_match_score(workout, activity)
        if score > best_score:
            best_score = score
            best_activity = activity

    return best_activity, best_score


class AdherenceTracker:
    """Tracks adherence between planned workouts and actual activities."""

    def __init__(self, repo: Repository):
        self.repo = repo

    def reconcile_date(self, target_date: date) -> list[tuple[int, int, float]]:
        """Match activities to planned workouts for a specific date.

        Returns list of tuples: (workout_id, activity_id, match_score)
        """
        # Get unmatched planned workouts for the date
        workouts = self.repo.get_unmatched_planned_workouts_for_date(target_date)
        if not workouts:
            return []

        # Get activities for the date
        activities = self.repo.get_activities_for_date(target_date)
        if not activities:
            return []

        matches = []
        used_activity_ids = set()

        # Match each workout to best available activity
        for workout in workouts:
            # Filter out already-matched activities
            available_activities = [a for a in activities if a.id not in used_activity_ids]
            if not available_activities:
                break

            best_activity, score = _find_best_match(workout, available_activities)

            # Only match if score is above minimum threshold (types must match = 0.5)
            if best_activity and score >= 0.5:
                self.repo.match_activity_to_workout(workout.id, best_activity.id)
                matches.append((workout.id, best_activity.id, score))
                used_activity_ids.add(best_activity.id)

        return matches

    def get_adherence_stats(self, start_date: date, end_date: date) -> dict:
        """Get adherence statistics for a date range."""
        workouts = self.repo.get_planned_workouts_range(start_date, end_date)
        total = len(workouts)

        # Count by status
        status_counts = {"completed": 0, "skipped": 0, "planned": 0}
        for w in workouts:
            if w.status in status_counts:
                status_counts[w.status] += 1

        completion_rate = (status_counts["completed"] / total * 100) if total > 0 else 0

        return {
            "total": total,
            "completed": status_counts["completed"],
            "skipped": status_counts["skipped"],
            "pending": status_counts["planned"],
            "completion_rate": round(completion_rate, 1),
        }
