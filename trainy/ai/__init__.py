"""Trainy AI integration."""

from .openrouter import generate_workouts, WorkoutSchema, WorkoutsResponse

__all__ = ["generate_workouts", "WorkoutSchema", "WorkoutsResponse"]
