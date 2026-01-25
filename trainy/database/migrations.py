"""Database schema and migrations."""

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 7

SCHEMA = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Activities - Parsed from FIT files
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY,
    fit_file_hash TEXT UNIQUE,
    fit_file_path TEXT,
    start_time DATETIME NOT NULL,
    end_time DATETIME,

    activity_type TEXT NOT NULL,
    source TEXT,

    duration_seconds REAL NOT NULL,
    distance_meters REAL,
    avg_speed_mps REAL,
    max_speed_mps REAL,

    total_ascent_m REAL,
    total_descent_m REAL,

    avg_hr INTEGER,
    max_hr INTEGER,

    avg_power REAL,
    max_power REAL,
    normalized_power REAL,

    avg_cadence INTEGER,

    calories INTEGER,

    title TEXT,
    imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    raw_fit_data BLOB
);

CREATE INDEX IF NOT EXISTS idx_activities_start_time ON activities(start_time);
CREATE INDEX IF NOT EXISTS idx_activities_type ON activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_activities_hash ON activities(fit_file_hash);

-- Activity metrics - Computed values
CREATE TABLE IF NOT EXISTS activity_metrics (
    id INTEGER PRIMARY KEY,
    activity_id INTEGER UNIQUE REFERENCES activities(id) ON DELETE CASCADE,

    tss REAL,
    tss_method TEXT,
    intensity_factor REAL,

    -- Efficiency metrics
    efficiency_factor REAL,
    variability_index REAL,

    peak_power_5s REAL,
    peak_power_1min REAL,
    peak_power_5min REAL,
    peak_power_20min REAL,

    -- Rowing-specific power peaks
    peak_power_4min REAL,
    peak_power_30min REAL,
    peak_power_60min REAL,

    -- Rowing distance PRs: best time (seconds) to cover each distance
    rowing_500m_time REAL,
    rowing_1k_time REAL,
    rowing_2k_time REAL,
    rowing_5k_time REAL,
    rowing_10k_time REAL,

    -- Rowing time PRs: best distance (meters) covered in each duration
    rowing_1min_distance REAL,
    rowing_4min_distance REAL,
    rowing_10min_distance REAL,
    rowing_20min_distance REAL,
    rowing_30min_distance REAL,
    rowing_60min_distance REAL,

    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_activity_metrics_activity ON activity_metrics(activity_id);

-- Daily metrics - Rolling aggregates
CREATE TABLE IF NOT EXISTS daily_metrics (
    date DATE PRIMARY KEY,
    total_tss REAL DEFAULT 0,
    activity_count INTEGER DEFAULT 0,
    total_duration_s REAL DEFAULT 0,
    total_distance_m REAL DEFAULT 0,

    ctl REAL,
    atl REAL,
    tsb REAL,

    tss_7day REAL,
    tss_30day REAL,
    tss_90day REAL,

    -- ACWR (Acute:Chronic Workload Ratio)
    acwr REAL,

    -- Monotony & Strain (Foster method)
    monotony REAL,
    strain REAL
);

-- User profile - Threshold values
CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY,
    ftp INTEGER DEFAULT 200,
    lthr INTEGER DEFAULT 165,
    max_hr INTEGER DEFAULT 185,
    resting_hr INTEGER DEFAULT 50,
    threshold_pace_minkm REAL DEFAULT 5.0,
    swim_threshold_pace REAL DEFAULT 2.0,
    weight_kg REAL DEFAULT 70,
    effective_from DATE NOT NULL,
    metrics_dirty BOOLEAN DEFAULT TRUE
);

-- Planned workouts - Future workouts (standalone, no plan grouping)
CREATE TABLE IF NOT EXISTS planned_workouts (
    id INTEGER PRIMARY KEY,

    planned_date DATE NOT NULL,
    activity_type TEXT NOT NULL,
    workout_type TEXT,

    title TEXT NOT NULL,
    description TEXT,
    structured_workout TEXT,

    target_duration_s REAL,
    target_distance_m REAL,
    target_tss REAL,
    target_calories INTEGER,
    target_hr_zone INTEGER,
    target_pace_minkm REAL,

    status TEXT DEFAULT 'planned',
    completed_activity_id INTEGER REFERENCES activities(id),

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_planned_workouts_date ON planned_workouts(planned_date);
CREATE INDEX IF NOT EXISTS idx_planned_workouts_date_type ON planned_workouts(planned_date, activity_type);

-- Workout feedback - User input
CREATE TABLE IF NOT EXISTS workout_feedback (
    id INTEGER PRIMARY KEY,
    activity_id INTEGER REFERENCES activities(id),
    planned_workout_id INTEGER REFERENCES planned_workouts(id),

    rpe INTEGER,
    comfort_level INTEGER,
    energy_level INTEGER,
    motivation INTEGER,

    sleep_hours REAL,
    sleep_quality INTEGER,
    muscle_soreness INTEGER,
    fatigue_level INTEGER,

    has_pain BOOLEAN DEFAULT FALSE,
    pain_location TEXT,
    pain_severity INTEGER,

    notes TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_workout_feedback_activity ON workout_feedback(activity_id);

-- User settings for wellness tracking
CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY,

    -- Morning check-in toggles
    morning_checkin_enabled BOOLEAN DEFAULT FALSE,
    morning_sleep_quality_enabled BOOLEAN DEFAULT FALSE,
    morning_sleep_hours_enabled BOOLEAN DEFAULT FALSE,
    morning_muscle_soreness_enabled BOOLEAN DEFAULT FALSE,
    morning_energy_enabled BOOLEAN DEFAULT FALSE,
    morning_mood_enabled BOOLEAN DEFAULT FALSE,

    -- Post-workout feedback toggles
    post_workout_feedback_enabled BOOLEAN DEFAULT FALSE,
    post_workout_rpe_enabled BOOLEAN DEFAULT FALSE,
    post_workout_pain_enabled BOOLEAN DEFAULT FALSE,
    post_workout_session_feel_enabled BOOLEAN DEFAULT FALSE,
    post_workout_notes_enabled BOOLEAN DEFAULT FALSE
);

-- Morning check-in (one per day, not tied to activities)
CREATE TABLE IF NOT EXISTS morning_checkin (
    id INTEGER PRIMARY KEY,
    checkin_date DATE UNIQUE NOT NULL,

    sleep_quality INTEGER,
    sleep_hours REAL,
    muscle_soreness INTEGER,
    energy_level INTEGER,
    mood INTEGER,

    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_morning_checkin_date ON morning_checkin(checkin_date);
"""


def init_database(db_path: Path) -> sqlite3.Connection:
    """Initialize the database with schema if needed."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    # Check if we need to initialize
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    if cursor.fetchone() is None:
        # Fresh database - apply schema
        conn.executescript(SCHEMA)
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
        conn.commit()
    else:
        # Check version for migrations
        cursor = conn.execute("SELECT MAX(version) FROM schema_version")
        current_version = cursor.fetchone()[0] or 0
        if current_version < SCHEMA_VERSION:
            _apply_migrations(conn, current_version, SCHEMA_VERSION)

    return conn


def _apply_migrations(conn: sqlite3.Connection, from_version: int, to_version: int) -> None:
    """Apply incremental migrations."""
    if from_version < 2 <= to_version:
        _migrate_v1_to_v2(conn)

    if from_version < 3 <= to_version:
        _migrate_v2_to_v3(conn)

    if from_version < 4 <= to_version:
        _migrate_v3_to_v4(conn)

    if from_version < 5 <= to_version:
        _migrate_v4_to_v5(conn)

    if from_version < 6 <= to_version:
        _migrate_v5_to_v6(conn)

    if from_version < 7 <= to_version:
        _migrate_v6_to_v7(conn)

    conn.execute("INSERT INTO schema_version (version) VALUES (?)", (to_version,))
    conn.commit()


def _migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    """Migration from v1 to v2: Add efficiency metrics and ACWR/monotony/strain fields."""
    # Add efficiency metrics to activity_metrics table
    try:
        conn.execute("ALTER TABLE activity_metrics ADD COLUMN efficiency_factor REAL")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        conn.execute("ALTER TABLE activity_metrics ADD COLUMN variability_index REAL")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add ACWR, monotony, strain to daily_metrics table
    try:
        conn.execute("ALTER TABLE daily_metrics ADD COLUMN acwr REAL")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        conn.execute("ALTER TABLE daily_metrics ADD COLUMN monotony REAL")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        conn.execute("ALTER TABLE daily_metrics ADD COLUMN strain REAL")
    except sqlite3.OperationalError:
        pass  # Column already exists


def _migrate_v2_to_v3(conn: sqlite3.Connection) -> None:
    """Migration from v2 to v3: Remove training_schemas, make planned_workouts standalone."""
    # Check if old planned_workouts table exists with training_schema_id column
    cursor = conn.execute("PRAGMA table_info(planned_workouts)")
    columns = {row[1] for row in cursor.fetchall()}

    if "training_schema_id" in columns:
        # Migrate existing data: create new table, copy data, swap tables
        conn.execute("""
            CREATE TABLE planned_workouts_new (
                id INTEGER PRIMARY KEY,
                planned_date DATE NOT NULL,
                activity_type TEXT NOT NULL,
                workout_type TEXT,
                title TEXT NOT NULL,
                description TEXT,
                structured_workout TEXT,
                target_duration_s REAL,
                target_distance_m REAL,
                target_tss REAL,
                target_hr_zone INTEGER,
                target_pace_minkm REAL,
                status TEXT DEFAULT 'planned',
                completed_activity_id INTEGER REFERENCES activities(id),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            INSERT INTO planned_workouts_new (
                id, planned_date, activity_type, workout_type, title, description,
                structured_workout, target_duration_s, target_distance_m, target_tss,
                target_hr_zone, target_pace_minkm, status, completed_activity_id, created_at
            )
            SELECT
                id, planned_date, activity_type, workout_type, title, description,
                structured_workout, target_duration_s, target_distance_m, target_tss,
                target_hr_zone, target_pace_minkm, status, completed_activity_id, created_at
            FROM planned_workouts
        """)

        conn.execute("DROP TABLE planned_workouts")
        conn.execute("ALTER TABLE planned_workouts_new RENAME TO planned_workouts")

        conn.execute("CREATE INDEX idx_planned_workouts_date ON planned_workouts(planned_date)")
        conn.execute("CREATE INDEX idx_planned_workouts_date_type ON planned_workouts(planned_date, activity_type)")

    # Drop training_schemas table if it exists (regardless of whether we migrated)
    conn.execute("DROP TABLE IF EXISTS training_schemas")


def _migrate_v3_to_v4(conn: sqlite3.Connection) -> None:
    """Migration from v3 to v4: Add user_settings and morning_checkin tables for wellness tracking."""
    # Create user_settings table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY,
            morning_checkin_enabled BOOLEAN DEFAULT FALSE,
            morning_sleep_quality_enabled BOOLEAN DEFAULT FALSE,
            morning_sleep_hours_enabled BOOLEAN DEFAULT FALSE,
            morning_muscle_soreness_enabled BOOLEAN DEFAULT FALSE,
            morning_energy_enabled BOOLEAN DEFAULT FALSE,
            morning_mood_enabled BOOLEAN DEFAULT FALSE,
            post_workout_feedback_enabled BOOLEAN DEFAULT FALSE,
            post_workout_rpe_enabled BOOLEAN DEFAULT FALSE,
            post_workout_pain_enabled BOOLEAN DEFAULT FALSE,
            post_workout_session_feel_enabled BOOLEAN DEFAULT FALSE,
            post_workout_notes_enabled BOOLEAN DEFAULT FALSE
        )
    """)

    # Create morning_checkin table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS morning_checkin (
            id INTEGER PRIMARY KEY,
            checkin_date DATE UNIQUE NOT NULL,
            sleep_quality INTEGER,
            sleep_hours REAL,
            muscle_soreness INTEGER,
            energy_level INTEGER,
            mood INTEGER,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_morning_checkin_date ON morning_checkin(checkin_date)")


def _migrate_v4_to_v5(conn: sqlite3.Connection) -> None:
    """Migration from v4 to v5: Add target_calories to planned_workouts."""
    try:
        conn.execute("ALTER TABLE planned_workouts ADD COLUMN target_calories INTEGER")
    except sqlite3.OperationalError:
        pass  # Column already exists


def _migrate_v5_to_v6(conn: sqlite3.Connection) -> None:
    """Migration from v5 to v6: Add rowing-specific power peak columns."""
    for col in ["peak_power_4min", "peak_power_30min", "peak_power_60min"]:
        try:
            conn.execute(f"ALTER TABLE activity_metrics ADD COLUMN {col} REAL")
        except sqlite3.OperationalError:
            pass  # Column already exists


def _migrate_v6_to_v7(conn: sqlite3.Connection) -> None:
    """Migration from v6 to v7: Add rowing best effort columns."""
    # Distance PRs: best time to cover each distance
    distance_cols = [
        "rowing_500m_time",
        "rowing_1k_time",
        "rowing_2k_time",
        "rowing_5k_time",
        "rowing_10k_time",
    ]
    # Time PRs: best distance covered in each duration
    time_cols = [
        "rowing_1min_distance",
        "rowing_4min_distance",
        "rowing_10min_distance",
        "rowing_20min_distance",
        "rowing_30min_distance",
        "rowing_60min_distance",
    ]
    for col in distance_cols + time_cols:
        try:
            conn.execute(f"ALTER TABLE activity_metrics ADD COLUMN {col} REAL")
        except sqlite3.OperationalError:
            pass  # Column already exists
