"""Coaching tool definitions and executors for LLM tool-calling."""

from datetime import date, timedelta
from typing import Any, Callable

from trainy.database import Repository
from trainy.database.models import PlannedWorkout
from trainy.metrics.planned_tss import calculate_planned_tss
from trainy.metrics.calories import predict_calories


# Tool definitions in OpenAI/OpenRouter format
COACHING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_recent_activities",
            "description": "Get past workouts with metrics from the last N days. Use this to understand recent training load, workout patterns, and performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default 30, max 90)",
                        "default": 30,
                    }
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fitness_state",
            "description": "Get current fitness metrics including CTL (chronic training load), ATL (acute training load), TSB (form), and ACWR (injury risk). Use this to assess readiness and fatigue.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pain_history",
            "description": "Get injury and pain patterns from workout feedback. Use this to identify recurring issues and avoid aggravating injuries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default 90)",
                        "default": 90,
                    }
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_wellness_trends",
            "description": "Get sleep, energy, mood, and soreness trends from morning check-ins. Use this to understand recovery and readiness patterns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default 14)",
                        "default": 14,
                    }
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_power_curve",
            "description": "Get best power efforts analysis for cycling. Use this to understand power capabilities at different durations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to analyze (default 90)",
                        "default": 90,
                    }
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_planned_workouts",
            "description": "Get upcoming planned workouts. Use this to see the current schedule and avoid conflicts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look ahead (default 14)",
                        "default": 14,
                    }
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_workouts",
            "description": "Create new planned workouts. Use this to add workouts to the training plan. Returns a proposal that needs user acceptance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "workouts": {
                        "type": "array",
                        "description": "List of workouts to create",
                        "items": {
                            "type": "object",
                            "properties": {
                                "date": {
                                    "type": "string",
                                    "description": "Date in YYYY-MM-DD format",
                                },
                                "activity_type": {
                                    "type": "string",
                                    "enum": ["run", "cycle", "swim", "row", "walk", "hike", "strength", "cardio", "yoga", "xcski", "ski", "snowboard", "other", "rest"],
                                    "description": "Type of activity",
                                },
                                "workout_type": {
                                    "type": "string",
                                    "enum": ["easy", "tempo", "intervals", "long", "recovery", "rest"],
                                    "description": "Type of workout",
                                },
                                "title": {
                                    "type": "string",
                                    "description": "Short title for the workout",
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Detailed workout description with instructions",
                                },
                                "target_duration_minutes": {
                                    "type": "integer",
                                    "description": "Target duration in minutes",
                                },
                            },
                            "required": ["date", "activity_type", "workout_type", "title", "description", "target_duration_minutes"],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["workouts"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "modify_workout",
            "description": "Modify an existing planned workout. Use this to update workout details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "workout_id": {
                        "type": "integer",
                        "description": "ID of the workout to modify",
                    },
                    "date": {
                        "type": "string",
                        "description": "New date in YYYY-MM-DD format (optional)",
                    },
                    "activity_type": {
                        "type": "string",
                        "enum": ["run", "cycle", "swim", "row", "walk", "hike", "strength", "cardio", "yoga", "xcski", "ski", "snowboard", "other", "rest"],
                        "description": "New activity type (optional)",
                    },
                    "workout_type": {
                        "type": "string",
                        "enum": ["easy", "tempo", "intervals", "long", "recovery", "rest"],
                        "description": "New workout type (optional)",
                    },
                    "title": {
                        "type": "string",
                        "description": "New title (optional)",
                    },
                    "description": {
                        "type": "string",
                        "description": "New description (optional)",
                    },
                    "target_duration_minutes": {
                        "type": "integer",
                        "description": "New target duration in minutes (optional)",
                    },
                },
                "required": ["workout_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_workout",
            "description": "Delete a planned workout. Use this to remove a workout from the schedule.",
            "parameters": {
                "type": "object",
                "properties": {
                    "workout_id": {
                        "type": "integer",
                        "description": "ID of the workout to delete",
                    }
                },
                "required": ["workout_id"],
                "additionalProperties": False,
            },
        },
    },
]

# Tool type categorization
READ_TOOLS = {"get_recent_activities", "get_fitness_state", "get_pain_history", "get_wellness_trends", "get_power_curve", "get_planned_workouts"}
WRITE_TOOLS = {"create_workouts", "modify_workout", "delete_workout"}


def execute_get_recent_activities(repo: Repository, days: int = 30) -> dict[str, Any]:
    """Get recent activities with metrics."""
    days = min(days, 90)  # Cap at 90 days
    activities = repo.get_recent_activities_with_metrics(days=days)

    activity_list = []
    for a in activities:
        activity_list.append({
            "date": a.start_time.strftime("%Y-%m-%d"),
            "type": a.activity_type,
            "title": a.title,
            "duration_minutes": round(a.duration_seconds / 60) if a.duration_seconds else 0,
            "distance_km": round(a.distance_meters / 1000, 1) if a.distance_meters else None,
            "avg_hr": a.avg_hr,
            "avg_power": a.avg_power,
            "tss": round(a.tss) if a.tss else None,
            "elevation_m": round(a.total_ascent_m) if a.total_ascent_m else None,
        })

    # Generate human-readable summary
    total_activities = len(activity_list)
    total_tss = sum(a.get("tss") or 0 for a in activity_list)
    by_type = {}
    for a in activity_list:
        t = a["type"]
        by_type[t] = by_type.get(t, 0) + 1

    summary = f"Found {total_activities} activities in the last {days} days"
    if total_tss:
        summary += f", total TSS: {total_tss}"
    if by_type:
        breakdown = ", ".join(f"{count} {t}" for t, count in sorted(by_type.items(), key=lambda x: -x[1]))
        summary += f" ({breakdown})"

    return {
        "activities": activity_list,
        "summary": summary,
    }


def execute_get_fitness_state(repo: Repository) -> dict[str, Any]:
    """Get current fitness metrics."""
    metrics = repo.get_latest_daily_metrics()

    if not metrics:
        return {
            "fitness": None,
            "summary": "No fitness data available yet. Need to import activities first.",
        }

    fitness = {
        "date": metrics.date.isoformat(),
        "ctl": round(metrics.ctl, 1) if metrics.ctl else 0,
        "atl": round(metrics.atl, 1) if metrics.atl else 0,
        "tsb": round(metrics.tsb, 1) if metrics.tsb else 0,
        "tss_7day": round(metrics.tss_7day) if metrics.tss_7day else 0,
        "tss_30day": round(metrics.tss_30day) if metrics.tss_30day else 0,
        "acwr": round(metrics.acwr, 2) if metrics.acwr else None,
    }

    # Interpret TSB (form)
    tsb = fitness["tsb"]
    if tsb > 25:
        form_status = "very fresh (possibly detrained)"
    elif tsb > 5:
        form_status = "fresh and ready"
    elif tsb > -10:
        form_status = "neutral"
    elif tsb > -30:
        form_status = "fatigued but manageable"
    else:
        form_status = "very fatigued (recovery needed)"

    # Interpret ACWR
    acwr = fitness["acwr"]
    if acwr is None:
        acwr_status = "unknown"
    elif acwr < 0.8:
        acwr_status = "undertraining"
    elif acwr <= 1.3:
        acwr_status = "optimal range"
    elif acwr <= 1.5:
        acwr_status = "elevated injury risk"
    else:
        acwr_status = "high injury risk"

    summary = f"CTL: {fitness['ctl']}, ATL: {fitness['atl']}, TSB: {fitness['tsb']} ({form_status})"
    if acwr:
        summary += f", ACWR: {acwr} ({acwr_status})"

    return {
        "fitness": fitness,
        "form_status": form_status,
        "acwr_status": acwr_status,
        "summary": summary,
    }


def execute_get_pain_history(repo: Repository, days: int = 90) -> dict[str, Any]:
    """Get pain/injury history."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    events = repo.get_pain_events_for_range(start_date, end_date)
    by_location = repo.get_pain_summary_by_location(start_date, end_date)
    by_activity = repo.get_pain_summary_by_activity_type(start_date, end_date)

    pain_events = [
        {
            "date": e["date"],
            "location": e["pain_location"],
            "severity": e["pain_severity"],
            "activity_type": e["activity_type"],
        }
        for e in events
    ]

    location_summary = [
        {
            "location": loc["location"],
            "count": loc["count"],
            "avg_severity": loc["avg_severity"],
        }
        for loc in by_location
    ]

    activity_summary = [
        {
            "activity_type": act["activity_type"],
            "count": act["count"],
            "avg_severity": act["avg_severity"],
        }
        for act in by_activity
    ]

    total = len(pain_events)
    if total == 0:
        summary = f"No pain events recorded in the last {days} days."
    else:
        summary = f"Found {total} pain events in the last {days} days"
        if location_summary:
            top_locations = ", ".join(f"{loc['location']} ({loc['count']}x)" for loc in location_summary[:3])
            summary += f". Most affected: {top_locations}"

    return {
        "pain_events": pain_events,
        "by_location": location_summary,
        "by_activity": activity_summary,
        "total_events": total,
        "summary": summary,
    }


def execute_get_wellness_trends(repo: Repository, days: int = 14) -> dict[str, Any]:
    """Get wellness trends from morning check-ins."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    checkins = repo.get_morning_checkins_range(start_date, end_date)

    checkin_data = []
    sleep_quality_sum = 0
    sleep_hours_sum = 0
    energy_sum = 0
    soreness_sum = 0
    valid_sleep_quality = 0
    valid_sleep_hours = 0
    valid_energy = 0
    valid_soreness = 0

    for c in checkins:
        entry = {
            "date": c.checkin_date.isoformat(),
            "sleep_quality": c.sleep_quality,
            "sleep_hours": c.sleep_hours,
            "energy_level": c.energy_level,
            "muscle_soreness": c.muscle_soreness,
            "mood": c.mood,
        }
        checkin_data.append(entry)

        if c.sleep_quality:
            sleep_quality_sum += c.sleep_quality
            valid_sleep_quality += 1
        if c.sleep_hours:
            sleep_hours_sum += c.sleep_hours
            valid_sleep_hours += 1
        if c.energy_level:
            energy_sum += c.energy_level
            valid_energy += 1
        if c.muscle_soreness:
            soreness_sum += c.muscle_soreness
            valid_soreness += 1

    averages = {}
    if valid_sleep_quality:
        averages["avg_sleep_quality"] = round(sleep_quality_sum / valid_sleep_quality, 1)
    if valid_sleep_hours:
        averages["avg_sleep_hours"] = round(sleep_hours_sum / valid_sleep_hours, 1)
    if valid_energy:
        averages["avg_energy"] = round(energy_sum / valid_energy, 1)
    if valid_soreness:
        averages["avg_soreness"] = round(soreness_sum / valid_soreness, 1)

    total = len(checkin_data)
    if total == 0:
        summary = f"No wellness check-ins recorded in the last {days} days."
    else:
        parts = [f"{total} check-ins"]
        if "avg_sleep_quality" in averages:
            parts.append(f"avg sleep quality: {averages['avg_sleep_quality']}/10")
        if "avg_sleep_hours" in averages:
            parts.append(f"avg sleep: {averages['avg_sleep_hours']}h")
        if "avg_energy" in averages:
            parts.append(f"avg energy: {averages['avg_energy']}/10")
        summary = ", ".join(parts)

    return {
        "checkins": checkin_data,
        "averages": averages,
        "total_checkins": total,
        "summary": summary,
    }


def execute_get_power_curve(repo: Repository, days: int = 90) -> dict[str, Any]:
    """Get power curve data."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Get all peak powers from the period
    peaks = repo.get_peak_powers_for_range(start_date, end_date)

    if not peaks:
        return {
            "power_curve": None,
            "summary": f"No cycling power data available in the last {days} days.",
        }

    # Find best for each duration
    best_5s = max((p["peak_power_5s"] for p in peaks if p.get("peak_power_5s")), default=None)
    best_1min = max((p["peak_power_1min"] for p in peaks if p.get("peak_power_1min")), default=None)
    best_5min = max((p["peak_power_5min"] for p in peaks if p.get("peak_power_5min")), default=None)
    best_20min = max((p["peak_power_20min"] for p in peaks if p.get("peak_power_20min")), default=None)

    # Get user profile for W/kg
    profile = repo.get_current_profile()
    weight_kg = profile.weight_kg if profile and profile.weight_kg > 0 else None

    curve = {
        "5s": {"watts": round(best_5s) if best_5s else None, "wpkg": round(best_5s / weight_kg, 2) if best_5s and weight_kg else None},
        "1min": {"watts": round(best_1min) if best_1min else None, "wpkg": round(best_1min / weight_kg, 2) if best_1min and weight_kg else None},
        "5min": {"watts": round(best_5min) if best_5min else None, "wpkg": round(best_5min / weight_kg, 2) if best_5min and weight_kg else None},
        "20min": {"watts": round(best_20min) if best_20min else None, "wpkg": round(best_20min / weight_kg, 2) if best_20min and weight_kg else None},
    }

    summary_parts = []
    if best_5s:
        summary_parts.append(f"5s: {round(best_5s)}W")
    if best_1min:
        summary_parts.append(f"1min: {round(best_1min)}W")
    if best_5min:
        summary_parts.append(f"5min: {round(best_5min)}W")
    if best_20min:
        summary_parts.append(f"20min: {round(best_20min)}W")

    summary = f"Best power in last {days} days: " + ", ".join(summary_parts) if summary_parts else "No power data"

    return {
        "power_curve": curve,
        "weight_kg": weight_kg,
        "ftp": profile.ftp if profile else None,
        "summary": summary,
    }


def execute_get_planned_workouts(repo: Repository, days: int = 14) -> dict[str, Any]:
    """Get upcoming planned workouts."""
    workouts = repo.get_upcoming_planned_workouts(days=days)

    workout_list = []
    total_tss = 0
    for w in workouts:
        workout_list.append({
            "id": w.id,
            "date": w.planned_date.isoformat(),
            "activity_type": w.activity_type,
            "workout_type": w.workout_type,
            "title": w.title,
            "description": w.description,
            "target_duration_minutes": round(w.target_duration_s / 60) if w.target_duration_s else None,
            "target_tss": round(w.target_tss) if w.target_tss else None,
            "status": w.status,
        })
        if w.target_tss:
            total_tss += w.target_tss

    total = len(workout_list)
    if total == 0:
        summary = f"No planned workouts in the next {days} days."
    else:
        summary = f"{total} workouts planned for next {days} days"
        if total_tss:
            summary += f", total planned TSS: {round(total_tss)}"

    return {
        "workouts": workout_list,
        "total_workouts": total,
        "total_planned_tss": round(total_tss) if total_tss else 0,
        "summary": summary,
    }


def execute_create_workouts(repo: Repository, workouts: list[dict]) -> dict[str, Any]:
    """Create workout proposals (doesn't save until accepted)."""
    profile = repo.get_current_profile()

    proposals = []
    for w in workouts:
        duration_s = w.get("target_duration_minutes", 60) * 60

        # Calculate TSS and intensity factor
        tss, intensity_factor = calculate_planned_tss(
            duration_s=duration_s,
            activity_type=w["activity_type"],
            workout_type=w["workout_type"],
            profile=profile,
        )

        # Calculate calories if we have weight
        calories = None
        if profile and profile.weight_kg > 0:
            calories = predict_calories(
                duration_s=duration_s,
                activity_type=w["activity_type"],
                intensity_factor=intensity_factor,
                weight_kg=profile.weight_kg,
            )

        proposals.append({
            "date": w["date"],
            "activity_type": w["activity_type"],
            "workout_type": w["workout_type"],
            "title": w["title"],
            "description": w["description"],
            "target_duration_minutes": w.get("target_duration_minutes", 60),
            "target_tss": round(tss) if tss else None,
            "target_calories": calories,
            "existing_workout_id": None,
        })

    summary = f"Created proposal with {len(proposals)} workout(s)"
    dates = sorted(set(p["date"] for p in proposals))
    if dates:
        summary += f" for {dates[0]}" + (f" to {dates[-1]}" if len(dates) > 1 else "")

    return {
        "proposals": proposals,
        "summary": summary,
        "requires_acceptance": True,
    }


def execute_modify_workout(repo: Repository, workout_id: int, **updates) -> dict[str, Any]:
    """Create a modification proposal for an existing workout."""
    existing = repo.get_planned_workout_by_id(workout_id)
    if not existing:
        return {
            "error": f"Workout with ID {workout_id} not found",
            "summary": f"Could not find workout #{workout_id}",
        }

    profile = repo.get_current_profile()

    # Build the modified workout
    new_date = updates.get("date", existing.planned_date.isoformat())
    new_activity_type = updates.get("activity_type", existing.activity_type)
    new_workout_type = updates.get("workout_type", existing.workout_type)
    new_title = updates.get("title", existing.title)
    new_description = updates.get("description", existing.description)
    new_duration_min = updates.get("target_duration_minutes")
    if new_duration_min is None and existing.target_duration_s:
        new_duration_min = round(existing.target_duration_s / 60)
    elif new_duration_min is None:
        new_duration_min = 60

    duration_s = new_duration_min * 60

    # Recalculate TSS
    tss, intensity_factor = calculate_planned_tss(
        duration_s=duration_s,
        activity_type=new_activity_type,
        workout_type=new_workout_type,
        profile=profile,
    )

    # Calculate calories
    calories = None
    if profile and profile.weight_kg > 0:
        calories = predict_calories(
            duration_s=duration_s,
            activity_type=new_activity_type,
            intensity_factor=intensity_factor,
            weight_kg=profile.weight_kg,
        )

    proposal = {
        "date": new_date if isinstance(new_date, str) else new_date.isoformat(),
        "activity_type": new_activity_type,
        "workout_type": new_workout_type,
        "title": new_title,
        "description": new_description,
        "target_duration_minutes": new_duration_min,
        "target_tss": round(tss) if tss else None,
        "target_calories": calories,
        "existing_workout_id": workout_id,
    }

    summary = f"Modified workout #{workout_id}: {new_title}"

    return {
        "proposals": [proposal],
        "summary": summary,
        "requires_acceptance": True,
    }


def execute_delete_workout(repo: Repository, workout_id: int) -> dict[str, Any]:
    """Create a deletion proposal for a workout."""
    existing = repo.get_planned_workout_by_id(workout_id)
    if not existing:
        return {
            "error": f"Workout with ID {workout_id} not found",
            "summary": f"Could not find workout #{workout_id}",
        }

    return {
        "deletion": {
            "workout_id": workout_id,
            "title": existing.title,
            "date": existing.planned_date.isoformat(),
        },
        "summary": f"Marked workout #{workout_id} ({existing.title} on {existing.planned_date}) for deletion",
        "requires_acceptance": True,
    }


# Tool executor registry
TOOL_EXECUTORS: dict[str, Callable] = {
    "get_recent_activities": execute_get_recent_activities,
    "get_fitness_state": execute_get_fitness_state,
    "get_pain_history": execute_get_pain_history,
    "get_wellness_trends": execute_get_wellness_trends,
    "get_power_curve": execute_get_power_curve,
    "get_planned_workouts": execute_get_planned_workouts,
    "create_workouts": execute_create_workouts,
    "modify_workout": execute_modify_workout,
    "delete_workout": execute_delete_workout,
}


def execute_tool(tool_name: str, repo: Repository, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool by name with given arguments."""
    executor = TOOL_EXECUTORS.get(tool_name)
    if not executor:
        return {"error": f"Unknown tool: {tool_name}", "summary": f"Tool '{tool_name}' not found"}

    try:
        return executor(repo, **arguments)
    except Exception as e:
        return {"error": str(e), "summary": f"Error executing {tool_name}: {e}"}
