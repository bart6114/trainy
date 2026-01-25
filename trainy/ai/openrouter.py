"""OpenRouter AI integration for workout generation."""

import copy
import json
from datetime import date
from typing import Any, Literal, Optional

import httpx
from pydantic import BaseModel

from ..config import settings
from ..database.models import PlannedWorkout, UserProfile
from ..metrics.planned_tss import calculate_planned_tss
from ..metrics.calories import predict_calories


# Default model for coaching
DEFAULT_MODEL = "anthropic/claude-opus-4.5"


def _make_schema_strict(schema: dict) -> dict:
    """Recursively add additionalProperties: false to all object types.

    Required by Anthropic's structured output API.
    """
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
    activity_type: Literal["run", "cycle", "swim", "row", "walk", "hike", "strength", "cardio", "yoga", "xcski", "ski", "snowboard", "other", "rest"]
    workout_type: Literal["easy", "tempo", "intervals", "long", "recovery", "rest"]
    title: str
    description: str
    target_duration_minutes: int
    existing_workout_id: Optional[int] = None  # Set if editing an existing workout


class WorkoutsWithExplanationResponse(BaseModel):
    """Schema for AI-generated workouts with explanation."""

    workouts: list[WorkoutSchema]
    explanation: str


class AnalysisResponse(BaseModel):
    """AI's analysis - either ready to generate or needs clarification."""

    ready_to_generate: bool
    clarifying_question: str | None = None
    question_options: list[str] | None = None


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


async def generate_workouts_with_context(
    user_prompt: str,
    recent_activities: list[dict],
    current_fitness: dict,
    existing_workouts: list[dict],
    conversation_history: list[dict],
    is_refinement: bool = False,
    profile: Optional[UserProfile] = None,
) -> Optional[tuple[list[dict], str]]:
    """Generate workouts with existing workout context and conversation history.

    Args:
        user_prompt: User's training goal description
        recent_activities: Summary of recent activities
        current_fitness: Current CTL/ATL/TSB values
        existing_workouts: Already planned workouts (to avoid conflicts)
        conversation_history: Previous messages in the conversation
        is_refinement: Whether this is refining an existing proposal
        profile: User profile with threshold values (for TSS/calorie calculation)

    Returns:
        Tuple of (list of workout dicts with existing_workout_id, assistant explanation) or None if generation fails
    """
    if not settings.has_openrouter_key:
        return None

    # Build context including existing workouts
    context = _build_context_with_existing(
        user_prompt,
        recent_activities,
        current_fitness,
        existing_workouts,
        is_refinement,
    )

    # Build the system prompt
    system_prompt = """You are an expert endurance coach creating personalized training workouts.

You create workouts that:
- Progress gradually (no more than 10% weekly volume increase)
- Include appropriate recovery days
- Balance different workout types (easy, tempo, intervals, long)
- Consider the athlete's current fitness level (CTL/ATL/TSB)
- Are specific and actionable
- Consider already planned workouts (multiple workouts per day are allowed)

When creating workouts:
- Easy runs: HR Zone 2, conversational pace
- Tempo runs: HR Zone 3-4, comfortably hard
- Intervals: HR Zone 4-5, with appropriate recovery
- Long runs: HR Zone 2, building aerobic base
- Recovery: Very easy or complete rest

EDITING EXISTING WORKOUTS:
- The user may ask to modify an existing planned workout (e.g., "make tomorrow's workout shorter")
- Already planned workouts are shown with [ID:N] prefixes in the context
- To edit an existing workout, include its ID in the `existing_workout_id` field
- If creating a new workout, leave `existing_workout_id` as null

Always respond with a valid JSON object containing:
1. An array of workouts (with existing_workout_id set for edits)
2. A brief explanation of your plan (2-3 sentences max)"""

    # Build messages with conversation history
    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history
    for msg in conversation_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current request
    messages.append({"role": "user", "content": context})

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
                    "model": "google/gemini-3-flash-preview",
                    "messages": messages,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "workouts_with_explanation",
                            "strict": True,
                            "schema": _make_schema_strict(
                                WorkoutsWithExplanationResponse.model_json_schema()
                            ),
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

            if "error" in result:
                print(f"OpenRouter returned error: {result['error']}")
                return None

            choices = result.get("choices", [])
            if not choices:
                print(f"OpenRouter returned no choices: {result}")
                return None

            content = choices[0].get("message", {}).get("content", "")
            if not content:
                print(f"OpenRouter returned empty content: {result}")
                return None

            data = json.loads(content)
            workouts_response = WorkoutsWithExplanationResponse.model_validate(data)

            # Convert to workout dicts and calculate TSS/calories
            workouts = []
            for w in workouts_response.workouts:
                duration_s = w.target_duration_minutes * 60

                # Calculate TSS and intensity factor
                tss, intensity_factor = calculate_planned_tss(
                    duration_s=duration_s,
                    activity_type=w.activity_type,
                    workout_type=w.workout_type,
                    profile=profile,
                )

                # Calculate calories if we have weight
                calories = None
                if profile and profile.weight_kg > 0:
                    calories = predict_calories(
                        duration_s=duration_s,
                        activity_type=w.activity_type,
                        intensity_factor=intensity_factor,
                        weight_kg=profile.weight_kg,
                    )

                workouts.append({
                    "date": w.date.isoformat(),
                    "activity_type": w.activity_type,
                    "workout_type": w.workout_type,
                    "title": w.title,
                    "description": w.description,
                    "target_duration_minutes": w.target_duration_minutes,
                    "target_tss": round(tss) if tss else None,
                    "target_calories": calories,
                    "existing_workout_id": w.existing_workout_id,
                })

            return (workouts, workouts_response.explanation)

    except Exception as e:
        print(f"Error generating workouts: {e}")
        return None


async def analyze_before_generation(
    user_prompt: str,
    recent_activities: list[dict],
    current_fitness: dict,
    existing_workouts: list[dict],
    conversation_history: list[dict],
) -> Optional[AnalysisResponse]:
    """First-pass analysis to determine if clarification needed.

    Args:
        user_prompt: User's training goal description
        recent_activities: Summary of recent activities
        current_fitness: Current CTL/ATL/TSB values
        existing_workouts: Already planned workouts (to avoid conflicts)
        conversation_history: Previous messages in the conversation

    Returns:
        AnalysisResponse indicating if ready to generate or needs clarification
    """
    if not settings.has_openrouter_key:
        return None

    # Build context string
    context = _build_analysis_context(
        user_prompt,
        recent_activities,
        current_fitness,
        existing_workouts,
    )

    system_prompt = """You are analyzing a workout planning request. Review the context and decide:

1. If you need clarification before creating workouts, respond with:
   - ready_to_generate: false
   - clarifying_question: Your question
   - question_options: ["Option 1", "Option 2", ...] (optional, 2-4 options)

2. If you have enough information, respond with:
   - ready_to_generate: true

Consider asking about:
- Conflicts with existing planned workouts (e.g., "You have workouts planned on Mon/Wed. Should I schedule around those or add additional sessions?")
- Ambiguous duration or frequency (e.g., "How many days per week would you like to train?")
- Missing key info (goal race date, available days, etc.)
- Significant fitness concerns (very negative TSB, recent overtraining)

Be concise. Only ask if genuinely needed - don't ask just to be thorough.
If the user has already answered a question in the conversation history, don't ask it again."""

    # Build messages with conversation history
    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history
    for msg in conversation_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current request
    messages.append({"role": "user", "content": context})

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "google/gemini-3-flash-preview",
                    "messages": messages,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "analysis_response",
                            "strict": True,
                            "schema": _make_schema_strict(
                                AnalysisResponse.model_json_schema()
                            ),
                        },
                    },
                    "max_tokens": 500,
                },
                timeout=30.0,
            )

            if response.status_code != 200:
                print(f"OpenRouter API error: {response.status_code} - {response.text}")
                return None

            result = response.json()

            if "error" in result:
                print(f"OpenRouter returned error: {result['error']}")
                return None

            choices = result.get("choices", [])
            if not choices:
                print(f"OpenRouter returned no choices: {result}")
                return None

            content = choices[0].get("message", {}).get("content", "")
            if not content:
                print(f"OpenRouter returned empty content: {result}")
                return None

            data = json.loads(content)
            return AnalysisResponse.model_validate(data)

    except Exception as e:
        print(f"Error in analysis: {e}")
        return None


def _build_analysis_context(
    user_prompt: str,
    recent_activities: list[dict],
    current_fitness: dict,
    existing_workouts: list[dict],
) -> str:
    """Build the context string for analysis phase."""
    today = date.today()

    # Format existing workouts (include ID for reference)
    existing_summary = ""
    if existing_workouts:
        lines = []
        for w in existing_workouts:
            duration_str = f"{w.get('target_duration_min', '?')}min" if w.get('target_duration_min') else ""
            workout_id = w.get('id', '')
            id_prefix = f"[ID:{workout_id}] " if workout_id else ""
            lines.append(
                f"- {id_prefix}{w.get('date', 'N/A')}: {w.get('title', 'N/A')} "
                f"({w.get('activity_type', 'N/A')}/{w.get('workout_type', 'N/A')}) {duration_str}"
            )
        existing_summary = "\n".join(lines)
    else:
        existing_summary = "No existing planned workouts."

    # Format current fitness
    fitness_summary = f"""CTL: {current_fitness.get('ctl', 0):.1f}, ATL: {current_fitness.get('atl', 0):.1f}, TSB: {current_fitness.get('tsb', 0):.1f}"""

    # Recent activity count
    activity_count = len(recent_activities) if recent_activities else 0

    return f"""Analyze this workout planning request:

## User Request
{user_prompt}

## Today's Date
{today.isoformat()}

## Current Fitness
{fitness_summary}

## Recent Training
{activity_count} activities in the last 60 days.

## Already Planned Workouts
{existing_summary}

Decide if you have enough information to generate workouts, or if you need to ask a clarifying question first."""


def _build_context_with_existing(
    user_prompt: str,
    recent_activities: list[dict],
    current_fitness: dict,
    existing_workouts: list[dict],
    is_refinement: bool,
) -> str:
    """Build the context string including existing workouts."""
    # Format recent activities
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

    # Format existing workouts (include ID for editing)
    existing_summary = ""
    if existing_workouts:
        lines = []
        for w in existing_workouts:
            duration_str = f"{w.get('target_duration_min', '?')}min" if w.get('target_duration_min') else ""
            workout_id = w.get('id', '')
            id_prefix = f"[ID:{workout_id}] " if workout_id else ""
            lines.append(
                f"- {id_prefix}{w.get('date', 'N/A')}: {w.get('title', 'N/A')} "
                f"({w.get('activity_type', 'N/A')}/{w.get('workout_type', 'N/A')}) {duration_str}"
            )
        existing_summary = "\n".join(lines)
    else:
        existing_summary = "No existing planned workouts."

    today = date.today()

    if is_refinement:
        instruction = """Please modify the workout plan based on the user's feedback.
Keep what works, adjust what they asked to change.
Make sure the overall plan still makes sense after the changes."""
    else:
        instruction = """Create ONLY the workouts explicitly requested by the user.
- If they ask for "tomorrow", generate exactly 1 workout for tomorrow
- If they ask for "this week", generate workouts for this week only
- If they ask for "a 4-week plan", then generate 4 weeks
- Never generate more workouts than explicitly requested
- Do not assume a default duration - ask for clarification if unclear

Include appropriate progression and recovery within the requested timeframe.
Consider the already planned workouts when creating the schedule.

If the user asks to modify an existing planned workout, include its ID in `existing_workout_id`.
Reference workouts by their ID from the 'Already Planned Workouts' section."""

    return f"""{"Refine" if is_refinement else "Create"} training workouts based on the following:

## User Request
{user_prompt}

## Today's Date
{today.isoformat()}

## Current Fitness Status
{fitness_summary}

## Recent Training (last 60 days)
{activities_summary}

## Already Planned Workouts
{existing_summary}

{instruction}

Respond with a JSON object containing:
1. "workouts": array of workout objects
2. "explanation": brief explanation of your plan (2-3 sentences)"""


async def chat_with_tools(
    messages: list[dict],
    tools: list[dict],
    model: str = DEFAULT_MODEL,
) -> Optional[dict[str, Any]]:
    """Call the LLM with tool-calling support.

    Args:
        messages: Conversation messages including system prompt
        tools: List of tool definitions in OpenAI format
        model: Model to use (default: Gemini 2.5 Flash)

    Returns:
        Dict with 'message' (assistant response) and 'finish_reason',
        or None if request failed.
    """
    if not settings.has_openrouter_key:
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "tools": tools,
                    "max_tokens": 8000,
                },
                timeout=120.0,
            )

            if response.status_code != 200:
                print(f"OpenRouter API error: {response.status_code} - {response.text}")
                return {"error": f"API error: {response.status_code}"}

            result = response.json()

            if "error" in result:
                print(f"OpenRouter returned error: {result['error']}")
                return {"error": str(result["error"])}

            choices = result.get("choices", [])
            if not choices:
                print(f"OpenRouter returned no choices: {result}")
                return {"error": "No response generated"}

            choice = choices[0]
            return {
                "message": choice.get("message", {}),
                "finish_reason": choice.get("finish_reason", ""),
            }

    except Exception as e:
        print(f"Error in chat_with_tools: {e}")
        return {"error": str(e)}
