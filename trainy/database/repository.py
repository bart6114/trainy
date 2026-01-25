"""Data access layer for the database."""

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from .migrations import init_database
from .models import (
    Activity,
    ActivityMetrics,
    DailyMetrics,
    UserProfile,
    PlannedWorkout,
    WorkoutFeedback,
    UserSettings,
    MorningCheckin,
)


class Repository:
    """Data access layer for all database operations."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = init_database(db_path)

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()

    # --- Activities ---

    def insert_activity(self, activity: Activity) -> int:
        """Insert a new activity, returns the ID."""
        cursor = self.conn.execute(
            """
            INSERT INTO activities (
                fit_file_hash, fit_file_path, start_time, end_time,
                activity_type, source, duration_seconds, distance_meters,
                avg_speed_mps, max_speed_mps, total_ascent_m, total_descent_m,
                avg_hr, max_hr, avg_power, max_power, normalized_power,
                avg_cadence, calories, title, raw_fit_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                activity.fit_file_hash,
                activity.fit_file_path,
                activity.start_time.isoformat() if activity.start_time else None,
                activity.end_time.isoformat() if activity.end_time else None,
                activity.activity_type,
                activity.source,
                activity.duration_seconds,
                activity.distance_meters,
                activity.avg_speed_mps,
                activity.max_speed_mps,
                activity.total_ascent_m,
                activity.total_descent_m,
                activity.avg_hr,
                activity.max_hr,
                activity.avg_power,
                activity.max_power,
                activity.normalized_power,
                activity.avg_cadence,
                activity.calories,
                activity.title,
                activity.raw_fit_data,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_activity_by_hash(self, fit_file_hash: str) -> Optional[Activity]:
        """Get activity by FIT file hash."""
        cursor = self.conn.execute(
            "SELECT * FROM activities WHERE fit_file_hash = ?", (fit_file_hash,)
        )
        row = cursor.fetchone()
        return self._row_to_activity(row) if row else None

    def get_activity_by_id(self, activity_id: int) -> Optional[Activity]:
        """Get activity by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM activities WHERE id = ?", (activity_id,)
        )
        row = cursor.fetchone()
        return self._row_to_activity(row) if row else None

    def get_activities_by_date_range(
        self, start_date: date, end_date: date
    ) -> list[Activity]:
        """Get activities within a date range."""
        cursor = self.conn.execute(
            """
            SELECT * FROM activities
            WHERE DATE(start_time) >= ? AND DATE(start_time) <= ?
            ORDER BY start_time DESC
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )
        return [self._row_to_activity(row) for row in cursor.fetchall()]

    def get_activities_for_date(self, target_date: date) -> list[Activity]:
        """Get all activities for a specific date."""
        cursor = self.conn.execute(
            """
            SELECT * FROM activities
            WHERE DATE(start_time) = ?
            ORDER BY start_time
            """,
            (target_date.isoformat(),),
        )
        return [self._row_to_activity(row) for row in cursor.fetchall()]

    def get_all_activities(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> list[Activity]:
        """Get all activities with optional pagination."""
        query = "SELECT * FROM activities ORDER BY start_time DESC"
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        cursor = self.conn.execute(query)
        return [self._row_to_activity(row) for row in cursor.fetchall()]

    def get_activity_count(self) -> int:
        """Get total number of activities."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM activities")
        return cursor.fetchone()[0]

    def get_recent_activities(self, days: int = 30) -> list[Activity]:
        """Get activities from the last N days."""
        start_date = date.today() - timedelta(days=days)
        return self.get_activities_by_date_range(start_date, date.today())

    def get_recent_activities_with_metrics(self, days: int = 60) -> list[Activity]:
        """Get activities from the last N days with TSS joined from activity_metrics."""
        start_date = date.today() - timedelta(days=days)
        cursor = self.conn.execute(
            """
            SELECT a.*, m.tss
            FROM activities a
            LEFT JOIN activity_metrics m ON a.id = m.activity_id
            WHERE DATE(a.start_time) >= ? AND DATE(a.start_time) <= ?
            ORDER BY a.start_time DESC
            """,
            (start_date.isoformat(), date.today().isoformat()),
        )
        return [self._row_to_activity_with_tss(row) for row in cursor.fetchall()]

    def _row_to_activity_with_tss(self, row: sqlite3.Row) -> Activity:
        """Convert database row to Activity model including TSS from join."""
        activity = self._row_to_activity(row)
        activity.tss = row["tss"] if "tss" in row.keys() else None
        return activity

    def _row_to_activity(self, row: sqlite3.Row) -> Activity:
        """Convert database row to Activity model."""
        return Activity(
            id=row["id"],
            fit_file_hash=row["fit_file_hash"],
            fit_file_path=row["fit_file_path"],
            start_time=datetime.fromisoformat(row["start_time"]),
            end_time=datetime.fromisoformat(row["end_time"]) if row["end_time"] else None,
            activity_type=row["activity_type"],
            source=row["source"],
            duration_seconds=row["duration_seconds"],
            distance_meters=row["distance_meters"],
            avg_speed_mps=row["avg_speed_mps"],
            max_speed_mps=row["max_speed_mps"],
            total_ascent_m=row["total_ascent_m"],
            total_descent_m=row["total_descent_m"],
            avg_hr=row["avg_hr"],
            max_hr=row["max_hr"],
            avg_power=row["avg_power"],
            max_power=row["max_power"],
            normalized_power=row["normalized_power"],
            avg_cadence=row["avg_cadence"],
            calories=row["calories"],
            title=row["title"],
            imported_at=datetime.fromisoformat(row["imported_at"]) if row["imported_at"] else None,
            raw_fit_data=row["raw_fit_data"],
        )

    # --- Activity Metrics ---

    def insert_activity_metrics(self, metrics: ActivityMetrics) -> int:
        """Insert or update activity metrics."""
        cursor = self.conn.execute(
            """
            INSERT OR REPLACE INTO activity_metrics (
                activity_id, tss, tss_method, intensity_factor,
                efficiency_factor, variability_index,
                peak_power_5s, peak_power_1min, peak_power_5min, peak_power_20min,
                peak_power_4min, peak_power_30min, peak_power_60min,
                rowing_500m_time, rowing_1k_time, rowing_2k_time, rowing_5k_time, rowing_10k_time,
                rowing_1min_distance, rowing_4min_distance, rowing_10min_distance,
                rowing_20min_distance, rowing_30min_distance, rowing_60min_distance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                metrics.activity_id,
                metrics.tss,
                metrics.tss_method,
                metrics.intensity_factor,
                metrics.efficiency_factor,
                metrics.variability_index,
                metrics.peak_power_5s,
                metrics.peak_power_1min,
                metrics.peak_power_5min,
                metrics.peak_power_20min,
                metrics.peak_power_4min,
                metrics.peak_power_30min,
                metrics.peak_power_60min,
                metrics.rowing_500m_time,
                metrics.rowing_1k_time,
                metrics.rowing_2k_time,
                metrics.rowing_5k_time,
                metrics.rowing_10k_time,
                metrics.rowing_1min_distance,
                metrics.rowing_4min_distance,
                metrics.rowing_10min_distance,
                metrics.rowing_20min_distance,
                metrics.rowing_30min_distance,
                metrics.rowing_60min_distance,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_activity_metrics(self, activity_id: int) -> Optional[ActivityMetrics]:
        """Get metrics for an activity."""
        cursor = self.conn.execute(
            "SELECT * FROM activity_metrics WHERE activity_id = ?", (activity_id,)
        )
        row = cursor.fetchone()
        if row:
            keys = row.keys()
            return ActivityMetrics(
                id=row["id"],
                activity_id=row["activity_id"],
                tss=row["tss"],
                tss_method=row["tss_method"],
                intensity_factor=row["intensity_factor"],
                efficiency_factor=row["efficiency_factor"] if "efficiency_factor" in keys else None,
                variability_index=row["variability_index"] if "variability_index" in keys else None,
                peak_power_5s=row["peak_power_5s"],
                peak_power_1min=row["peak_power_1min"],
                peak_power_5min=row["peak_power_5min"],
                peak_power_20min=row["peak_power_20min"],
                peak_power_4min=row["peak_power_4min"] if "peak_power_4min" in keys else None,
                peak_power_30min=row["peak_power_30min"] if "peak_power_30min" in keys else None,
                peak_power_60min=row["peak_power_60min"] if "peak_power_60min" in keys else None,
                rowing_500m_time=row["rowing_500m_time"] if "rowing_500m_time" in keys else None,
                rowing_1k_time=row["rowing_1k_time"] if "rowing_1k_time" in keys else None,
                rowing_2k_time=row["rowing_2k_time"] if "rowing_2k_time" in keys else None,
                rowing_5k_time=row["rowing_5k_time"] if "rowing_5k_time" in keys else None,
                rowing_10k_time=row["rowing_10k_time"] if "rowing_10k_time" in keys else None,
                rowing_1min_distance=row["rowing_1min_distance"] if "rowing_1min_distance" in keys else None,
                rowing_4min_distance=row["rowing_4min_distance"] if "rowing_4min_distance" in keys else None,
                rowing_10min_distance=row["rowing_10min_distance"] if "rowing_10min_distance" in keys else None,
                rowing_20min_distance=row["rowing_20min_distance"] if "rowing_20min_distance" in keys else None,
                rowing_30min_distance=row["rowing_30min_distance"] if "rowing_30min_distance" in keys else None,
                rowing_60min_distance=row["rowing_60min_distance"] if "rowing_60min_distance" in keys else None,
                calculated_at=datetime.fromisoformat(row["calculated_at"]) if row["calculated_at"] else None,
            )
        return None

    def update_activity_tss(self, activity_id: int, tss: float, tss_method: str, intensity_factor: float) -> None:
        """Update TSS for an activity."""
        self.conn.execute(
            """
            INSERT OR REPLACE INTO activity_metrics (activity_id, tss, tss_method, intensity_factor, calculated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (activity_id, tss, tss_method, intensity_factor),
        )
        self.conn.commit()

    # --- Daily Metrics ---

    def upsert_daily_metrics(self, metrics: DailyMetrics) -> None:
        """Insert or update daily metrics."""
        self.conn.execute(
            """
            INSERT OR REPLACE INTO daily_metrics (
                date, total_tss, activity_count, total_duration_s, total_distance_m,
                ctl, atl, tsb, tss_7day, tss_30day, tss_90day,
                acwr, monotony, strain
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                metrics.date.isoformat(),
                metrics.total_tss,
                metrics.activity_count,
                metrics.total_duration_s,
                metrics.total_distance_m,
                metrics.ctl,
                metrics.atl,
                metrics.tsb,
                metrics.tss_7day,
                metrics.tss_30day,
                metrics.tss_90day,
                metrics.acwr,
                metrics.monotony,
                metrics.strain,
            ),
        )
        self.conn.commit()

    def get_daily_metrics(self, target_date: date) -> Optional[DailyMetrics]:
        """Get daily metrics for a specific date."""
        cursor = self.conn.execute(
            "SELECT * FROM daily_metrics WHERE date = ?", (target_date.isoformat(),)
        )
        row = cursor.fetchone()
        if row:
            return self._row_to_daily_metrics(row)
        return None

    def _row_to_daily_metrics(self, row: sqlite3.Row) -> DailyMetrics:
        """Convert database row to DailyMetrics model."""
        keys = row.keys()
        return DailyMetrics(
            date=date.fromisoformat(row["date"]),
            total_tss=row["total_tss"] or 0,
            activity_count=row["activity_count"] or 0,
            total_duration_s=row["total_duration_s"] or 0,
            total_distance_m=row["total_distance_m"] or 0,
            ctl=row["ctl"],
            atl=row["atl"],
            tsb=row["tsb"],
            tss_7day=row["tss_7day"],
            tss_30day=row["tss_30day"],
            tss_90day=row["tss_90day"],
            acwr=row["acwr"] if "acwr" in keys else None,
            monotony=row["monotony"] if "monotony" in keys else None,
            strain=row["strain"] if "strain" in keys else None,
        )

    def get_daily_metrics_range(self, start_date: date, end_date: date) -> list[DailyMetrics]:
        """Get daily metrics for a date range."""
        cursor = self.conn.execute(
            """
            SELECT * FROM daily_metrics
            WHERE date >= ? AND date <= ?
            ORDER BY date
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )
        return [self._row_to_daily_metrics(row) for row in cursor.fetchall()]

    def get_latest_daily_metrics(self) -> Optional[DailyMetrics]:
        """Get the most recent daily metrics."""
        cursor = self.conn.execute(
            "SELECT * FROM daily_metrics ORDER BY date DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            return self._row_to_daily_metrics(row)
        return None

    # --- User Profile ---

    def get_current_profile(self) -> UserProfile:
        """Get the current user profile."""
        cursor = self.conn.execute(
            """
            SELECT * FROM user_profile
            WHERE effective_from <= DATE('now')
            ORDER BY effective_from DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        if row:
            return UserProfile(
                id=row["id"],
                ftp=row["ftp"],
                lthr=row["lthr"],
                max_hr=row["max_hr"],
                resting_hr=row["resting_hr"],
                threshold_pace_minkm=row["threshold_pace_minkm"],
                swim_threshold_pace=row["swim_threshold_pace"],
                weight_kg=row["weight_kg"],
                effective_from=date.fromisoformat(row["effective_from"]),
                metrics_dirty=bool(row["metrics_dirty"]),
            )
        # Return default profile if none exists
        return UserProfile()

    def save_profile(self, profile: UserProfile) -> int:
        """Save user profile, returns ID."""
        cursor = self.conn.execute(
            """
            INSERT INTO user_profile (
                ftp, lthr, max_hr, resting_hr, threshold_pace_minkm,
                swim_threshold_pace, weight_kg, effective_from, metrics_dirty
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile.ftp,
                profile.lthr,
                profile.max_hr,
                profile.resting_hr,
                profile.threshold_pace_minkm,
                profile.swim_threshold_pace,
                profile.weight_kg,
                profile.effective_from.isoformat(),
                profile.metrics_dirty,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_profile(self, profile: UserProfile) -> None:
        """Update existing profile."""
        self.conn.execute(
            """
            UPDATE user_profile SET
                ftp = ?, lthr = ?, max_hr = ?, resting_hr = ?,
                threshold_pace_minkm = ?, swim_threshold_pace = ?,
                weight_kg = ?, metrics_dirty = ?
            WHERE id = ?
            """,
            (
                profile.ftp,
                profile.lthr,
                profile.max_hr,
                profile.resting_hr,
                profile.threshold_pace_minkm,
                profile.swim_threshold_pace,
                profile.weight_kg,
                profile.metrics_dirty,
                profile.id,
            ),
        )
        self.conn.commit()

    def set_metrics_dirty(self, dirty: bool) -> None:
        """Set the metrics_dirty flag on the current profile."""
        self.conn.execute(
            """
            UPDATE user_profile SET metrics_dirty = ?
            WHERE id = (SELECT id FROM user_profile ORDER BY effective_from DESC LIMIT 1)
            """,
            (dirty,),
        )
        self.conn.commit()

    # --- Planned Workouts ---

    def insert_planned_workout(self, workout: PlannedWorkout) -> int:
        """Insert a planned workout."""
        cursor = self.conn.execute(
            """
            INSERT INTO planned_workouts (
                planned_date, activity_type, workout_type,
                title, description, structured_workout, target_duration_s,
                target_distance_m, target_tss, target_calories, target_hr_zone, target_pace_minkm,
                status, completed_activity_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                workout.planned_date.isoformat(),
                workout.activity_type,
                workout.workout_type,
                workout.title,
                workout.description,
                workout.structured_workout,
                workout.target_duration_s,
                workout.target_distance_m,
                workout.target_tss,
                workout.target_calories,
                workout.target_hr_zone,
                workout.target_pace_minkm,
                workout.status,
                workout.completed_activity_id,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def bulk_insert_planned_workouts(self, workouts: list[PlannedWorkout]) -> list[int]:
        """Insert multiple planned workouts in a batch."""
        return [self.insert_planned_workout(workout) for workout in workouts]

    def delete_planned_workout(self, workout_id: int) -> bool:
        """Delete a planned workout."""
        cursor = self.conn.execute(
            "DELETE FROM planned_workouts WHERE id = ?",
            (workout_id,),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def get_planned_workout_by_id(self, workout_id: int) -> Optional[PlannedWorkout]:
        """Get a planned workout by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM planned_workouts WHERE id = ?",
            (workout_id,),
        )
        row = cursor.fetchone()
        return self._row_to_planned_workout(row) if row else None

    def get_planned_workouts_for_date(self, target_date: date) -> list[PlannedWorkout]:
        """Get planned workouts for a specific date."""
        cursor = self.conn.execute(
            """
            SELECT * FROM planned_workouts
            WHERE planned_date = ?
            ORDER BY id
            """,
            (target_date.isoformat(),),
        )
        return [self._row_to_planned_workout(row) for row in cursor.fetchall()]

    def get_planned_workouts_range(
        self, start_date: date, end_date: date
    ) -> list[PlannedWorkout]:
        """Get planned workouts in a date range."""
        cursor = self.conn.execute(
            """
            SELECT * FROM planned_workouts
            WHERE planned_date >= ? AND planned_date <= ?
            ORDER BY planned_date
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )
        return [self._row_to_planned_workout(row) for row in cursor.fetchall()]

    def update_planned_workout_status(
        self, workout_id: int, status: str, completed_activity_id: Optional[int] = None
    ) -> None:
        """Update planned workout status."""
        self.conn.execute(
            """
            UPDATE planned_workouts
            SET status = ?, completed_activity_id = ?
            WHERE id = ?
            """,
            (status, completed_activity_id, workout_id),
        )
        self.conn.commit()

    def update_planned_workout(
        self,
        workout_id: int,
        planned_date: Optional[date] = None,
        activity_type: Optional[str] = None,
        workout_type: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        target_duration_s: Optional[float] = None,
        target_tss: Optional[float] = None,
        target_calories: Optional[int] = None,
    ) -> Optional[PlannedWorkout]:
        """Update a planned workout's fields. Only non-None values are updated."""
        # Build dynamic update query
        updates = []
        params = []

        if planned_date is not None:
            updates.append("planned_date = ?")
            params.append(planned_date.isoformat())
        if activity_type is not None:
            updates.append("activity_type = ?")
            params.append(activity_type)
        if workout_type is not None:
            updates.append("workout_type = ?")
            params.append(workout_type)
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if target_duration_s is not None:
            updates.append("target_duration_s = ?")
            params.append(target_duration_s)
        if target_tss is not None:
            updates.append("target_tss = ?")
            params.append(target_tss)
        if target_calories is not None:
            updates.append("target_calories = ?")
            params.append(target_calories)

        if not updates:
            return self.get_planned_workout_by_id(workout_id)

        params.append(workout_id)
        query = f"UPDATE planned_workouts SET {', '.join(updates)} WHERE id = ?"
        self.conn.execute(query, params)
        self.conn.commit()

        return self.get_planned_workout_by_id(workout_id)

    def _row_to_planned_workout(self, row: sqlite3.Row) -> PlannedWorkout:
        """Convert row to PlannedWorkout."""
        keys = row.keys()
        return PlannedWorkout(
            id=row["id"],
            planned_date=date.fromisoformat(row["planned_date"]),
            activity_type=row["activity_type"],
            workout_type=row["workout_type"],
            title=row["title"],
            description=row["description"],
            structured_workout=row["structured_workout"],
            target_duration_s=row["target_duration_s"],
            target_distance_m=row["target_distance_m"],
            target_tss=row["target_tss"],
            target_calories=row["target_calories"] if "target_calories" in keys else None,
            target_hr_zone=row["target_hr_zone"],
            target_pace_minkm=row["target_pace_minkm"],
            status=row["status"],
            completed_activity_id=row["completed_activity_id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
        )

    def get_upcoming_planned_workouts(self, days: int = 7) -> list[PlannedWorkout]:
        """Get planned workouts for the next N days."""
        start = date.today()
        end = start + timedelta(days=days)
        cursor = self.conn.execute(
            """
            SELECT * FROM planned_workouts
            WHERE planned_date >= ? AND planned_date <= ?
            AND status = 'planned'
            ORDER BY planned_date
            """,
            (start.isoformat(), end.isoformat()),
        )
        return [self._row_to_planned_workout(row) for row in cursor.fetchall()]

    def get_unmatched_planned_workouts_for_date(self, target_date: date) -> list[PlannedWorkout]:
        """Get planned workouts for a date that haven't been matched to an activity."""
        cursor = self.conn.execute(
            """
            SELECT * FROM planned_workouts
            WHERE planned_date = ? AND completed_activity_id IS NULL AND status = 'planned'
            ORDER BY id
            """,
            (target_date.isoformat(),),
        )
        return [self._row_to_planned_workout(row) for row in cursor.fetchall()]

    def match_activity_to_workout(self, workout_id: int, activity_id: int) -> None:
        """Link an activity to a planned workout."""
        self.conn.execute(
            """
            UPDATE planned_workouts
            SET status = 'completed', completed_activity_id = ?
            WHERE id = ?
            """,
            (activity_id, workout_id),
        )
        self.conn.commit()

    # --- Workout Feedback ---

    def insert_feedback(self, feedback: WorkoutFeedback) -> int:
        """Insert workout feedback."""
        cursor = self.conn.execute(
            """
            INSERT INTO workout_feedback (
                activity_id, planned_workout_id, rpe, comfort_level,
                energy_level, motivation, sleep_hours, sleep_quality,
                muscle_soreness, fatigue_level, has_pain, pain_location,
                pain_severity, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feedback.activity_id,
                feedback.planned_workout_id,
                feedback.rpe,
                feedback.comfort_level,
                feedback.energy_level,
                feedback.motivation,
                feedback.sleep_hours,
                feedback.sleep_quality,
                feedback.muscle_soreness,
                feedback.fatigue_level,
                feedback.has_pain,
                feedback.pain_location,
                feedback.pain_severity,
                feedback.notes,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_feedback_for_activity(self, activity_id: int) -> Optional[WorkoutFeedback]:
        """Get feedback for an activity."""
        cursor = self.conn.execute(
            "SELECT * FROM workout_feedback WHERE activity_id = ?", (activity_id,)
        )
        row = cursor.fetchone()
        if row:
            return WorkoutFeedback(
                id=row["id"],
                activity_id=row["activity_id"],
                planned_workout_id=row["planned_workout_id"],
                rpe=row["rpe"],
                comfort_level=row["comfort_level"],
                energy_level=row["energy_level"],
                motivation=row["motivation"],
                sleep_hours=row["sleep_hours"],
                sleep_quality=row["sleep_quality"],
                muscle_soreness=row["muscle_soreness"],
                fatigue_level=row["fatigue_level"],
                has_pain=bool(row["has_pain"]),
                pain_location=row["pain_location"],
                pain_severity=row["pain_severity"],
                notes=row["notes"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            )
        return None

    def update_feedback(self, feedback: WorkoutFeedback) -> None:
        """Update existing feedback."""
        self.conn.execute(
            """
            UPDATE workout_feedback SET
                rpe = ?, comfort_level = ?, energy_level = ?, motivation = ?,
                sleep_hours = ?, sleep_quality = ?, muscle_soreness = ?,
                fatigue_level = ?, has_pain = ?, pain_location = ?,
                pain_severity = ?, notes = ?
            WHERE id = ?
            """,
            (
                feedback.rpe,
                feedback.comfort_level,
                feedback.energy_level,
                feedback.motivation,
                feedback.sleep_hours,
                feedback.sleep_quality,
                feedback.muscle_soreness,
                feedback.fatigue_level,
                feedback.has_pain,
                feedback.pain_location,
                feedback.pain_severity,
                feedback.notes,
                feedback.id,
            ),
        )
        self.conn.commit()

    # --- Utility Methods ---

    def get_weekly_tss_totals(self, weeks: int = 12) -> list[dict]:
        """Get weekly TSS totals for the last N weeks.

        Returns list of dicts with 'week_start' and 'total_tss' keys.
        """
        cursor = self.conn.execute(
            """
            SELECT
                DATE(start_time, 'weekday 0', '-6 days') as week_start,
                COALESCE(SUM(m.tss), 0) as total_tss
            FROM activities a
            LEFT JOIN activity_metrics m ON a.id = m.activity_id
            WHERE DATE(start_time) >= DATE('now', ? || ' days')
            GROUP BY week_start
            ORDER BY week_start
            """,
            (f"-{weeks * 7}",),
        )
        return [
            {"week_start": row[0], "total_tss": round(row[1] or 0)}
            for row in cursor.fetchall()
        ]

    def get_daily_tss_series(self) -> list[tuple[date, float]]:
        """Get (date, total_tss) for all days with activities."""
        cursor = self.conn.execute(
            """
            SELECT DATE(a.start_time) as day, COALESCE(SUM(m.tss), 0) as daily_tss
            FROM activities a
            LEFT JOIN activity_metrics m ON a.id = m.activity_id
            GROUP BY DATE(a.start_time)
            ORDER BY day
            """
        )
        return [(date.fromisoformat(row[0]), row[1] or 0) for row in cursor.fetchall()]

    def rebuild_daily_metrics(self) -> None:
        """Rebuild all daily metrics from activities."""
        # Get all days with activities
        cursor = self.conn.execute(
            """
            SELECT DATE(start_time) as day,
                   COUNT(*) as count,
                   SUM(duration_seconds) as duration,
                   SUM(distance_meters) as distance
            FROM activities
            GROUP BY DATE(start_time)
            ORDER BY day
            """
        )

        daily_data = {}
        for row in cursor.fetchall():
            day = date.fromisoformat(row[0])
            daily_data[day] = {
                "count": row[1],
                "duration": row[2] or 0,
                "distance": row[3] or 0,
            }

        # Get TSS per day
        cursor = self.conn.execute(
            """
            SELECT DATE(a.start_time) as day, SUM(m.tss) as tss
            FROM activities a
            JOIN activity_metrics m ON a.id = m.activity_id
            GROUP BY DATE(a.start_time)
            """
        )
        for row in cursor.fetchall():
            day = date.fromisoformat(row[0])
            if day in daily_data:
                daily_data[day]["tss"] = row[1] or 0

        # Update daily_metrics table
        for day, data in daily_data.items():
            metrics = DailyMetrics(
                date=day,
                total_tss=data.get("tss", 0),
                activity_count=data["count"],
                total_duration_s=data["duration"],
                total_distance_m=data["distance"],
            )
            self.upsert_daily_metrics(metrics)

    def delete_all_activities(self) -> int:
        """Delete all activities and their metrics. Returns count deleted."""
        # First delete activity metrics
        self.conn.execute("DELETE FROM activity_metrics")
        # Then delete activities
        cursor = self.conn.execute("DELETE FROM activities")
        self.conn.commit()
        return cursor.rowcount

    def delete_all_daily_metrics(self) -> int:
        """Delete all daily metrics. Returns count deleted."""
        cursor = self.conn.execute("DELETE FROM daily_metrics")
        self.conn.commit()
        return cursor.rowcount

    def get_data_stats(self) -> dict:
        """Get counts of all data types for deletion confirmation UI."""
        activities = self.conn.execute("SELECT COUNT(*) FROM activities").fetchone()[0]
        planned_workouts = self.conn.execute("SELECT COUNT(*) FROM planned_workouts").fetchone()[0]
        activity_metrics = self.conn.execute("SELECT COUNT(*) FROM activity_metrics").fetchone()[0]
        daily_metrics = self.conn.execute("SELECT COUNT(*) FROM daily_metrics").fetchone()[0]
        workout_feedback = self.conn.execute("SELECT COUNT(*) FROM workout_feedback").fetchone()[0]
        return {
            "activities": activities,
            "planned_workouts": planned_workouts,
            "activity_metrics": activity_metrics,
            "daily_metrics": daily_metrics,
            "workout_feedback": workout_feedback,
        }

    def delete_all_planned_workouts(self) -> int:
        """Delete all planned workouts and orphaned feedback. Returns count deleted."""
        # Delete orphaned workout feedback (where activity_id IS NULL)
        self.conn.execute("DELETE FROM workout_feedback WHERE activity_id IS NULL")
        # Delete all planned workouts
        cursor = self.conn.execute("DELETE FROM planned_workouts")
        self.conn.commit()
        return cursor.rowcount

    def delete_all_user_data(self) -> dict:
        """Delete all user data except profile. Returns counts deleted."""
        # Delete in order respecting foreign keys
        feedback_count = self.conn.execute("DELETE FROM workout_feedback").rowcount
        activity_metrics_count = self.conn.execute("DELETE FROM activity_metrics").rowcount
        daily_metrics_count = self.conn.execute("DELETE FROM daily_metrics").rowcount
        planned_workouts_count = self.conn.execute("DELETE FROM planned_workouts").rowcount
        activities_count = self.conn.execute("DELETE FROM activities").rowcount
        self.conn.commit()
        return {
            "activities": activities_count,
            "planned_workouts": planned_workouts_count,
            "activity_metrics": activity_metrics_count,
            "daily_metrics": daily_metrics_count,
            "workout_feedback": feedback_count,
        }

    def get_peak_powers_for_range(self, start_date: date, end_date: date) -> list[dict]:
        """Get best peak powers for each duration within a date range."""
        cursor = self.conn.execute(
            """
            SELECT m.peak_power_5s, m.peak_power_1min, m.peak_power_5min, m.peak_power_20min,
                   a.id as activity_id, DATE(a.start_time) as activity_date
            FROM activity_metrics m
            JOIN activities a ON m.activity_id = a.id
            WHERE DATE(a.start_time) >= ? AND DATE(a.start_time) <= ?
              AND a.activity_type = 'cycle'
              AND (m.peak_power_5s IS NOT NULL OR m.peak_power_1min IS NOT NULL
                   OR m.peak_power_5min IS NOT NULL OR m.peak_power_20min IS NOT NULL)
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_rowing_activities_with_fit_paths(self) -> list[dict]:
        """Get all rowing activities that have FIT file paths."""
        cursor = self.conn.execute(
            """
            SELECT id, fit_file_path, DATE(start_time) as start_date
            FROM activities
            WHERE activity_type = 'row'
              AND fit_file_path IS NOT NULL
            ORDER BY start_time DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_rowing_distance_prs(self) -> list[dict]:
        """Get best rowing times for standard distances (500m, 1k, 2k, 5k, 10k).

        Uses a 2% tolerance to match distances (e.g., 4950-5050m for 5k).
        """
        distances = [
            (500, "500m", 0.02),
            (1000, "1k", 0.02),
            (2000, "2k", 0.02),
            (5000, "5k", 0.02),
            (10000, "10k", 0.02),
        ]

        results = []
        for target_m, label, tolerance in distances:
            min_dist = target_m * (1 - tolerance)
            max_dist = target_m * (1 + tolerance)

            cursor = self.conn.execute(
                """
                SELECT id, distance_meters, duration_seconds, DATE(start_time) as activity_date
                FROM activities
                WHERE activity_type = 'row'
                  AND distance_meters >= ? AND distance_meters <= ?
                  AND duration_seconds IS NOT NULL
                ORDER BY duration_seconds ASC
                LIMIT 1
                """,
                (min_dist, max_dist),
            )
            row = cursor.fetchone()
            if row:
                results.append({
                    "distance_meters": target_m,
                    "distance_label": label,
                    "total_seconds": row["duration_seconds"],
                    "activity_id": row["id"],
                    "activity_date": row["activity_date"],
                })
            else:
                results.append({
                    "distance_meters": target_m,
                    "distance_label": label,
                    "total_seconds": None,
                    "activity_id": None,
                    "activity_date": None,
                })

        return results

    def get_rowing_power_prs(self) -> list[dict]:
        """Get best rowing power at standard durations (1min, 4min, 30min, 60min)."""
        durations = [
            (60, "1min", "peak_power_1min"),
            (240, "4min", "peak_power_4min"),
            (1800, "30min", "peak_power_30min"),
            (3600, "60min", "peak_power_60min"),
        ]

        results = []
        for duration_s, label, column in durations:
            cursor = self.conn.execute(
                f"""
                SELECT m.{column} as power, a.id as activity_id, DATE(a.start_time) as activity_date
                FROM activity_metrics m
                JOIN activities a ON m.activity_id = a.id
                WHERE a.activity_type = 'row'
                  AND m.{column} IS NOT NULL
                ORDER BY m.{column} DESC
                LIMIT 1
                """,
            )
            row = cursor.fetchone()
            if row:
                results.append({
                    "duration_seconds": duration_s,
                    "duration_label": label,
                    "best_watts": row["power"],
                    "activity_id": row["activity_id"],
                    "activity_date": row["activity_date"],
                })
            else:
                results.append({
                    "duration_seconds": duration_s,
                    "duration_label": label,
                    "best_watts": None,
                    "activity_id": None,
                    "activity_date": None,
                })

        return results

    def get_rowing_prs_for_range(self, start_date: date, end_date: date) -> dict:
        """Get best rowing PRs within a date range from pre-computed activity_metrics.

        Returns a dict with:
        - distance_prs: list of dicts with best time for each distance
        - time_prs: list of dicts with best distance for each duration
        - power_prs: list of dicts with best power for each duration
        """
        # Distance PRs: best (lowest) time for each distance
        distance_targets = [
            (500, "500m", "rowing_500m_time"),
            (1000, "1k", "rowing_1k_time"),
            (2000, "2k", "rowing_2k_time"),
            (5000, "5k", "rowing_5k_time"),
            (10000, "10k", "rowing_10k_time"),
        ]

        distance_prs = []
        for target_m, label, column in distance_targets:
            cursor = self.conn.execute(
                f"""
                SELECT m.{column} as time, a.id as activity_id, DATE(a.start_time) as activity_date
                FROM activity_metrics m
                JOIN activities a ON m.activity_id = a.id
                WHERE a.activity_type = 'row'
                  AND DATE(a.start_time) >= ? AND DATE(a.start_time) <= ?
                  AND m.{column} IS NOT NULL
                ORDER BY m.{column} ASC
                LIMIT 1
                """,
                (start_date.isoformat(), end_date.isoformat()),
            )
            row = cursor.fetchone()
            if row:
                distance_prs.append({
                    "distance_meters": target_m,
                    "distance_label": label,
                    "total_seconds": row["time"],
                    "activity_id": row["activity_id"],
                    "activity_date": row["activity_date"],
                })
            else:
                distance_prs.append({
                    "distance_meters": target_m,
                    "distance_label": label,
                    "total_seconds": None,
                    "activity_id": None,
                    "activity_date": None,
                })

        # Time PRs: best (highest) distance for each duration
        time_targets = [
            (60, "1min", "rowing_1min_distance"),
            (240, "4min", "rowing_4min_distance"),
            (600, "10min", "rowing_10min_distance"),
            (1200, "20min", "rowing_20min_distance"),
            (1800, "30min", "rowing_30min_distance"),
            (3600, "60min", "rowing_60min_distance"),
        ]

        time_prs = []
        for target_s, label, column in time_targets:
            cursor = self.conn.execute(
                f"""
                SELECT m.{column} as distance, a.id as activity_id, DATE(a.start_time) as activity_date
                FROM activity_metrics m
                JOIN activities a ON m.activity_id = a.id
                WHERE a.activity_type = 'row'
                  AND DATE(a.start_time) >= ? AND DATE(a.start_time) <= ?
                  AND m.{column} IS NOT NULL
                ORDER BY m.{column} DESC
                LIMIT 1
                """,
                (start_date.isoformat(), end_date.isoformat()),
            )
            row = cursor.fetchone()
            if row:
                time_prs.append({
                    "duration_seconds": target_s,
                    "duration_label": label,
                    "best_distance_meters": row["distance"],
                    "activity_id": row["activity_id"],
                    "activity_date": row["activity_date"],
                })
            else:
                time_prs.append({
                    "duration_seconds": target_s,
                    "duration_label": label,
                    "best_distance_meters": None,
                    "activity_id": None,
                    "activity_date": None,
                })

        # Power PRs: best (highest) power for each duration
        power_targets = [
            (60, "1min", "peak_power_1min"),
            (240, "4min", "peak_power_4min"),
            (1800, "30min", "peak_power_30min"),
            (3600, "60min", "peak_power_60min"),
        ]

        power_prs = []
        for target_s, label, column in power_targets:
            cursor = self.conn.execute(
                f"""
                SELECT m.{column} as power, a.id as activity_id, DATE(a.start_time) as activity_date
                FROM activity_metrics m
                JOIN activities a ON m.activity_id = a.id
                WHERE a.activity_type = 'row'
                  AND DATE(a.start_time) >= ? AND DATE(a.start_time) <= ?
                  AND m.{column} IS NOT NULL
                ORDER BY m.{column} DESC
                LIMIT 1
                """,
                (start_date.isoformat(), end_date.isoformat()),
            )
            row = cursor.fetchone()
            if row:
                power_prs.append({
                    "duration_seconds": target_s,
                    "duration_label": label,
                    "best_watts": row["power"],
                    "activity_id": row["activity_id"],
                    "activity_date": row["activity_date"],
                })
            else:
                power_prs.append({
                    "duration_seconds": target_s,
                    "duration_label": label,
                    "best_watts": None,
                    "activity_id": None,
                    "activity_date": None,
                })

        return {
            "distance_prs": distance_prs,
            "time_prs": time_prs,
            "power_prs": power_prs,
        }

    def delete_activities_only(self) -> dict:
        """Delete activities and related data, preserving planned workouts. Returns counts deleted."""
        # Unlink completed activities from planned workouts
        self.conn.execute("""
            UPDATE planned_workouts
            SET completed_activity_id = NULL, status = 'planned'
            WHERE completed_activity_id IS NOT NULL
        """)
        # Delete activity-related feedback
        feedback_count = self.conn.execute("DELETE FROM workout_feedback WHERE activity_id IS NOT NULL").rowcount
        # Delete activity metrics (would be cascade but explicit is clearer)
        activity_metrics_count = self.conn.execute("DELETE FROM activity_metrics").rowcount
        # Delete daily metrics
        daily_metrics_count = self.conn.execute("DELETE FROM daily_metrics").rowcount
        # Delete activities
        activities_count = self.conn.execute("DELETE FROM activities").rowcount
        self.conn.commit()
        return {
            "activities": activities_count,
            "activity_metrics": activity_metrics_count,
            "daily_metrics": daily_metrics_count,
            "workout_feedback": feedback_count,
        }

    # --- User Settings (Wellness) ---

    def get_user_settings(self) -> UserSettings:
        """Get user settings, creating default if none exists."""
        cursor = self.conn.execute("SELECT * FROM user_settings LIMIT 1")
        row = cursor.fetchone()
        if row:
            return UserSettings(
                id=row["id"],
                morning_checkin_enabled=bool(row["morning_checkin_enabled"]),
                morning_sleep_quality_enabled=bool(row["morning_sleep_quality_enabled"]),
                morning_sleep_hours_enabled=bool(row["morning_sleep_hours_enabled"]),
                morning_muscle_soreness_enabled=bool(row["morning_muscle_soreness_enabled"]),
                morning_energy_enabled=bool(row["morning_energy_enabled"]),
                morning_mood_enabled=bool(row["morning_mood_enabled"]),
                post_workout_feedback_enabled=bool(row["post_workout_feedback_enabled"]),
                post_workout_rpe_enabled=bool(row["post_workout_rpe_enabled"]),
                post_workout_pain_enabled=bool(row["post_workout_pain_enabled"]),
                post_workout_session_feel_enabled=bool(row["post_workout_session_feel_enabled"]),
                post_workout_notes_enabled=bool(row["post_workout_notes_enabled"]),
            )
        return UserSettings()

    def update_user_settings(self, settings: UserSettings) -> UserSettings:
        """Update user settings, creating if none exists."""
        existing = self.conn.execute("SELECT id FROM user_settings LIMIT 1").fetchone()

        if existing:
            self.conn.execute(
                """
                UPDATE user_settings SET
                    morning_checkin_enabled = ?,
                    morning_sleep_quality_enabled = ?,
                    morning_sleep_hours_enabled = ?,
                    morning_muscle_soreness_enabled = ?,
                    morning_energy_enabled = ?,
                    morning_mood_enabled = ?,
                    post_workout_feedback_enabled = ?,
                    post_workout_rpe_enabled = ?,
                    post_workout_pain_enabled = ?,
                    post_workout_session_feel_enabled = ?,
                    post_workout_notes_enabled = ?
                WHERE id = ?
                """,
                (
                    settings.morning_checkin_enabled,
                    settings.morning_sleep_quality_enabled,
                    settings.morning_sleep_hours_enabled,
                    settings.morning_muscle_soreness_enabled,
                    settings.morning_energy_enabled,
                    settings.morning_mood_enabled,
                    settings.post_workout_feedback_enabled,
                    settings.post_workout_rpe_enabled,
                    settings.post_workout_pain_enabled,
                    settings.post_workout_session_feel_enabled,
                    settings.post_workout_notes_enabled,
                    existing["id"],
                ),
            )
            settings.id = existing["id"]
        else:
            cursor = self.conn.execute(
                """
                INSERT INTO user_settings (
                    morning_checkin_enabled, morning_sleep_quality_enabled,
                    morning_sleep_hours_enabled, morning_muscle_soreness_enabled,
                    morning_energy_enabled, morning_mood_enabled,
                    post_workout_feedback_enabled, post_workout_rpe_enabled,
                    post_workout_pain_enabled, post_workout_session_feel_enabled,
                    post_workout_notes_enabled
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    settings.morning_checkin_enabled,
                    settings.morning_sleep_quality_enabled,
                    settings.morning_sleep_hours_enabled,
                    settings.morning_muscle_soreness_enabled,
                    settings.morning_energy_enabled,
                    settings.morning_mood_enabled,
                    settings.post_workout_feedback_enabled,
                    settings.post_workout_rpe_enabled,
                    settings.post_workout_pain_enabled,
                    settings.post_workout_session_feel_enabled,
                    settings.post_workout_notes_enabled,
                ),
            )
            settings.id = cursor.lastrowid

        self.conn.commit()
        return settings

    # --- Morning Check-in ---

    def get_morning_checkin(self, checkin_date: date) -> Optional[MorningCheckin]:
        """Get morning check-in for a specific date."""
        cursor = self.conn.execute(
            "SELECT * FROM morning_checkin WHERE checkin_date = ?",
            (checkin_date.isoformat(),),
        )
        row = cursor.fetchone()
        if row:
            return MorningCheckin(
                id=row["id"],
                checkin_date=date.fromisoformat(row["checkin_date"]),
                sleep_quality=row["sleep_quality"],
                sleep_hours=row["sleep_hours"],
                muscle_soreness=row["muscle_soreness"],
                energy_level=row["energy_level"],
                mood=row["mood"],
                notes=row["notes"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            )
        return None

    def upsert_morning_checkin(self, checkin: MorningCheckin) -> MorningCheckin:
        """Insert or update morning check-in for a date."""
        existing = self.conn.execute(
            "SELECT id FROM morning_checkin WHERE checkin_date = ?",
            (checkin.checkin_date.isoformat(),),
        ).fetchone()

        if existing:
            self.conn.execute(
                """
                UPDATE morning_checkin SET
                    sleep_quality = ?,
                    sleep_hours = ?,
                    muscle_soreness = ?,
                    energy_level = ?,
                    mood = ?,
                    notes = ?
                WHERE id = ?
                """,
                (
                    checkin.sleep_quality,
                    checkin.sleep_hours,
                    checkin.muscle_soreness,
                    checkin.energy_level,
                    checkin.mood,
                    checkin.notes,
                    existing["id"],
                ),
            )
            checkin.id = existing["id"]
        else:
            cursor = self.conn.execute(
                """
                INSERT INTO morning_checkin (
                    checkin_date, sleep_quality, sleep_hours,
                    muscle_soreness, energy_level, mood, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checkin.checkin_date.isoformat(),
                    checkin.sleep_quality,
                    checkin.sleep_hours,
                    checkin.muscle_soreness,
                    checkin.energy_level,
                    checkin.mood,
                    checkin.notes,
                ),
            )
            checkin.id = cursor.lastrowid

        self.conn.commit()
        return checkin

    def get_morning_checkins_range(self, start_date: date, end_date: date) -> list[MorningCheckin]:
        """Get morning check-ins within a date range."""
        cursor = self.conn.execute(
            """
            SELECT * FROM morning_checkin
            WHERE checkin_date >= ? AND checkin_date <= ?
            ORDER BY checkin_date DESC
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )
        checkins = []
        for row in cursor.fetchall():
            checkins.append(MorningCheckin(
                id=row["id"],
                checkin_date=date.fromisoformat(row["checkin_date"]),
                sleep_quality=row["sleep_quality"],
                sleep_hours=row["sleep_hours"],
                muscle_soreness=row["muscle_soreness"],
                energy_level=row["energy_level"],
                mood=row["mood"],
                notes=row["notes"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            ))
        return checkins

    # --- Pending Feedback (for notification badge) ---

    def get_activities_without_feedback(self, days: int = 3) -> list[Activity]:
        """Get activities from the last N days that don't have feedback."""
        start_date = date.today() - timedelta(days=days)
        cursor = self.conn.execute(
            """
            SELECT a.* FROM activities a
            LEFT JOIN workout_feedback wf ON a.id = wf.activity_id
            WHERE DATE(a.start_time) >= ? AND DATE(a.start_time) <= ?
              AND wf.id IS NULL
            ORDER BY a.start_time DESC
            """,
            (start_date.isoformat(), date.today().isoformat()),
        )
        return [self._row_to_activity(row) for row in cursor.fetchall()]

    def upsert_activity_feedback(self, feedback: WorkoutFeedback) -> WorkoutFeedback:
        """Insert or update feedback for an activity."""
        if feedback.activity_id:
            existing = self.conn.execute(
                "SELECT id FROM workout_feedback WHERE activity_id = ?",
                (feedback.activity_id,),
            ).fetchone()

            if existing:
                feedback.id = existing["id"]
                self.update_feedback(feedback)
                return feedback

        feedback.id = self.insert_feedback(feedback)
        return feedback

    # --- Pain/Injury Analysis ---

    def get_pain_events_for_range(self, start_date: date, end_date: date) -> list[dict]:
        """Get pain events within a date range by joining workout_feedback and activities."""
        cursor = self.conn.execute(
            """
            SELECT
                DATE(a.start_time) as date,
                wf.pain_location,
                wf.pain_severity,
                a.activity_type,
                a.id as activity_id,
                a.title as activity_title
            FROM workout_feedback wf
            JOIN activities a ON wf.activity_id = a.id
            WHERE wf.has_pain = 1
              AND DATE(a.start_time) >= ? AND DATE(a.start_time) <= ?
            ORDER BY a.start_time DESC
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_pain_summary_by_location(self, start_date: date, end_date: date) -> list[dict]:
        """Get pain summary grouped by location."""
        cursor = self.conn.execute(
            """
            SELECT
                wf.pain_location as location,
                COUNT(*) as count,
                ROUND(AVG(wf.pain_severity), 1) as avg_severity,
                MAX(wf.pain_severity) as max_severity
            FROM workout_feedback wf
            JOIN activities a ON wf.activity_id = a.id
            WHERE wf.has_pain = 1
              AND DATE(a.start_time) >= ? AND DATE(a.start_time) <= ?
            GROUP BY wf.pain_location
            ORDER BY count DESC
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_pain_summary_by_activity_type(self, start_date: date, end_date: date) -> list[dict]:
        """Get pain summary grouped by activity type."""
        cursor = self.conn.execute(
            """
            SELECT
                a.activity_type,
                COUNT(*) as count,
                ROUND(AVG(wf.pain_severity), 1) as avg_severity
            FROM workout_feedback wf
            JOIN activities a ON wf.activity_id = a.id
            WHERE wf.has_pain = 1
              AND DATE(a.start_time) >= ? AND DATE(a.start_time) <= ?
            GROUP BY a.activity_type
            ORDER BY count DESC
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_unique_pain_locations(self) -> list[dict]:
        """Get unique pain locations with occurrence counts."""
        cursor = self.conn.execute(
            """
            SELECT
                pain_location as location,
                COUNT(*) as count
            FROM workout_feedback
            WHERE has_pain = 1 AND pain_location IS NOT NULL AND pain_location != ''
            GROUP BY pain_location
            ORDER BY count DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]

    def merge_pain_locations(self, sources: list[str], target: str) -> int:
        """Merge multiple pain locations into a single target location.

        Returns the number of updated records.
        """
        if not sources:
            return 0
        placeholders = ",".join("?" * len(sources))
        cursor = self.conn.execute(
            f"""
            UPDATE workout_feedback
            SET pain_location = ?
            WHERE pain_location IN ({placeholders})
            """,
            [target] + sources,
        )
        self.conn.commit()
        return cursor.rowcount
