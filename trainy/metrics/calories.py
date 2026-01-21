"""Caloric expenditure prediction for planned workouts."""


# MET values by activity type and intensity level
# Source: Compendium of Physical Activities
# Columns: Light (IF < 0.7), Moderate (0.7-0.9), Vigorous (> 0.9)
MET_VALUES = {
    "cycling": {"light": 6.0, "moderate": 8.0, "vigorous": 12.0},
    "cycle": {"light": 6.0, "moderate": 8.0, "vigorous": 12.0},
    "running": {"light": 8.0, "moderate": 10.0, "vigorous": 12.5},
    "run": {"light": 8.0, "moderate": 10.0, "vigorous": 12.5},
    "swimming": {"light": 6.0, "moderate": 8.0, "vigorous": 10.0},
    "swim": {"light": 6.0, "moderate": 8.0, "vigorous": 10.0},
    "strength": {"light": 3.5, "moderate": 5.0, "vigorous": 6.0},
}

# Default MET for unknown activity types
DEFAULT_MET = {"light": 5.0, "moderate": 6.5, "vigorous": 8.0}


def predict_calories(
    duration_s: float,
    activity_type: str,
    intensity_factor: float,
    weight_kg: float,
) -> int:
    """Predict caloric expenditure for a workout.

    Uses MET-based calculation:
    calories = MET × weight_kg × duration_hours

    The MET value is selected based on the intensity factor:
    - Light: IF < 0.7
    - Moderate: 0.7 <= IF <= 0.9
    - Vigorous: IF > 0.9

    Args:
        duration_s: Workout duration in seconds
        activity_type: Type of activity (run, cycle, swim, strength)
        intensity_factor: Intensity factor (0.5 - 1.5 typical range)
        weight_kg: User's body weight in kilograms

    Returns:
        Predicted caloric expenditure (integer)
    """
    if duration_s <= 0 or weight_kg <= 0:
        return 0

    # Get MET values for activity type
    met_values = MET_VALUES.get(activity_type.lower(), DEFAULT_MET)

    # Select MET based on intensity factor
    if intensity_factor < 0.7:
        met = met_values["light"]
    elif intensity_factor <= 0.9:
        met = met_values["moderate"]
    else:
        met = met_values["vigorous"]

    # Calculate calories: MET × weight × hours
    duration_hours = duration_s / 3600
    calories = met * weight_kg * duration_hours

    return round(calories)
