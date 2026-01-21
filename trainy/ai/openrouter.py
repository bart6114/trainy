"""OpenRouter AI integration for workout generation."""

from datetime import date
from typing import Literal, Optional

import httpx
from pydantic import BaseModel

from ..config import settings
from ..database.models import PlannedWorkout


def _make_schema_strict(schema: dict) -> dict:
    """Recursively add additionalProperties: false to all object types.

    Required by Anthropic's structured output API.
    """
    import copy
    schema = copy.deepcopy(schema)

    def _add_additional_properties(obj):
        if isinstance(obj, dict):
            if obj.get("type") == "object":
                obj["additionalProperties"] = False
            for value in obj.values():
                _add_additional_properties(value)
        elif isinstance(obj, list):
            for item in obj:
                _add_additional_properties(item)

    _add_additional_properties(schema)
    return schema


class WorkoutSchema(BaseModel):
    """Schema for a workout from AI generation."""

    date: date
    activity_type: Literal["run", "cycle", "swim", "strength", "rest"]
    workout_type: Literal["easy", "tempo", "intervals", "long", "recovery", "rest"]
    title: str
    description: str
    target_duration_minutes: int
    target_tss: Optional[int] = None


class WorkoutsResponse(BaseModel):
    """Schema for AI-generated workouts response."""

    workouts: list[WorkoutSchema]


async def generate_workouts(
    user_prompt: str,
    recent_activities: list[dict],
    current_fitness: dict,
) -> Optional[list[PlannedWorkout]]:
    """Generate workouts using OpenRouter API.

    Args:
        user_prompt: User's training goal description
        recent_activities: Summary of recent activities
        current_fitness: Current CTL/ATL/TSB values

    Returns:
        List of PlannedWorkout objects ready for DB insertion, or None if generation fails
    """
    if not settings.has_openrouter_key:
        return None

    # Build context for the AI
    context = _build_context(user_prompt, recent_activities, current_fitness)

    # Build the system prompt
    system_prompt = """You are an expert endurance coach creating personalized training workouts.

You create workouts that:
- Progress gradually (no more than 10% weekly volume increase)
- Include appropriate recovery days
- Balance different workout types (easy, tempo, intervals, long)
- Consider the athlete's current fitness level (CTL/ATL/TSB)
- Are specific and actionable

When creating workouts:
- Easy runs: HR Zone 2, conversational pace
- Tempo runs: HR Zone 3-4, comfortably hard
- Intervals: HR Zone 4-5, with appropriate recovery
- Long runs: HR Zone 2, building aerobic base
- Recovery: Very easy or complete rest

Always respond with a valid JSON object containing an array of workouts."""

    # Make API request with structured outputs
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "anthropic/claude-sonnet-4",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": context},
                    ],
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "workouts",
                            "strict": True,
                            "schema": _make_schema_strict(WorkoutsResponse.model_json_schema()),
                        },
                    },
                    "max_tokens": 8000,
                },
                timeout=120.0,
            )

            if response.status_code != 200:
                print(f"OpenRouter API error: {response.status_code} - {response.text}")
                return None

            result = response.json()

            # Check for error in response
            if "error" in result:
                print(f"OpenRouter returned error: {result['error']}")
                return None

            # Extract content from response
            choices = result.get("choices", [])
            if not choices:
                print(f"OpenRouter returned no choices: {result}")
                return None

            content = choices[0].get("message", {}).get("content", "")
            if not content:
                print(f"OpenRouter returned empty content: {result}")
                return None

            import json
            data = json.loads(content)
            workouts_response = WorkoutsResponse.model_validate(data)

            # Convert to PlannedWorkout models
            planned_workouts = []
            for w in workouts_response.workouts:
                workout = PlannedWorkout(
                    planned_date=w.date,
                    activity_type=w.activity_type,
                    workout_type=w.workout_type,
                    title=w.title,
                    description=w.description,
                    target_duration_s=w.target_duration_minutes * 60,
                    target_tss=w.target_tss,
                    status="planned",
                )
                planned_workouts.append(workout)

            return planned_workouts

    except Exception as e:
        print(f"Error generating workouts: {e}")
        return None


def _build_context(
    user_prompt: str,
    recent_activities: list[dict],
    current_fitness: dict,
) -> str:
    """Build the context string for the AI."""
    # Format recent activities with full metrics
    activities_summary = ""
    if recent_activities:
        lines = []
        for a in recent_activities:
            line = (
                f"- {a.get('date', 'N/A')}: {a.get('type', 'N/A')} - "
                f"{a.get('duration_min', 0):.0f}min, {a.get('distance_km', 0):.1f}km, "
                f"HR: {a.get('avg_hr') or '-'}/{a.get('max_hr') or '-'}, "
                f"Power: {a.get('avg_power') or '-'}W, Elev: {a.get('elevation_m') or '-'}m, "
                f"Cadence: {a.get('cadence') or '-'}, TSS: {a.get('tss') or '-'}"
            )
            lines.append(line)
        activities_summary = "\n".join(lines)
    else:
        activities_summary = "No recent activities available."

    # Format current fitness
    fitness_summary = f"""
CTL (Chronic Training Load): {current_fitness.get('ctl', 0):.1f}
ATL (Acute Training Load): {current_fitness.get('atl', 0):.1f}
TSB (Training Stress Balance): {current_fitness.get('tsb', 0):.1f}
7-day TSS: {current_fitness.get('tss_7day', 0):.0f}
30-day TSS: {current_fitness.get('tss_30day', 0):.0f}
"""

    today = date.today()

    return f"""Create training workouts based on the following:

## User Request
{user_prompt}

## Today's Date
{today.isoformat()}

## Current Fitness Status
{fitness_summary}

## Recent Training (last 60 days)
{activities_summary}

Please create specific workouts for each day.
Determine the appropriate duration based on the user's request (default to 4 weeks if not specified).
Include appropriate progression and recovery.

Respond with a JSON object containing a "workouts" array:
{{
  "workouts": [
    {{
      "date": "YYYY-MM-DD",
      "activity_type": "run|cycle|swim|strength|rest",
      "workout_type": "easy|tempo|intervals|long|recovery|rest",
      "title": "Workout title",
      "description": "Detailed workout description",
      "target_duration_minutes": 45,
      "target_tss": 50
    }}
  ]
}}"""


async def validate_api_key() -> bool:
    """Validate that the OpenRouter API key works."""
    if not settings.has_openrouter_key:
        return False

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                },
                timeout=10.0,
            )
            return response.status_code == 200
    except Exception:
        return False
