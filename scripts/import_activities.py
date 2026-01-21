#!/usr/bin/env python
"""CLI script for importing FIT files from RunGap."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from trainy.config import settings
from trainy.database import Repository
from trainy.database.models import ActivityMetrics
from trainy.importers import FitImporter, parse_fit_file, calculate_normalized_power
from trainy.metrics import calculate_tss, calculate_training_load
from trainy.metrics.efficiency import calculate_efficiency_factor, calculate_variability_index


def main():
    """Main import function."""
    print("=" * 60)
    print("Trainy - FIT File Importer")
    print("=" * 60)

    # Check RunGap path
    if not settings.rungap_exists:
        print(f"Error: RunGap path not found: {settings.rungap_path}")
        sys.exit(1)

    print(f"RunGap path: {settings.rungap_path}")

    # Initialize importer and database
    importer = FitImporter(settings.rungap_path)
    db = Repository(settings.database_path)

    # Get list of FIT files
    fit_files = importer.get_fit_files()
    total_files = len(fit_files)
    print(f"Found {total_files} FIT files to process")

    if total_files == 0:
        print("No FIT files found. Exiting.")
        return

    # Get user profile for TSS calculations
    profile = db.get_current_profile()
    if profile.id is None:
        print("Creating default user profile...")
        db.save_profile(profile)
        profile = db.get_current_profile()

    print(f"\nUser profile: FTP={profile.ftp}W, LTHR={profile.lthr}bpm, Threshold Pace={profile.threshold_pace_minkm}min/km")
    print()

    # Import activities
    imported = 0
    skipped = 0
    failed = 0

    for i, fit_file in enumerate(fit_files):
        # Progress indicator
        if (i + 1) % 100 == 0 or (i + 1) == total_files:
            print(f"Processing: {i + 1}/{total_files} ({imported} imported, {skipped} skipped, {failed} failed)")

        try:
            # Parse FIT file
            activity = parse_fit_file(fit_file, include_raw_data=False)

            if activity is None:
                failed += 1
                continue

            # Check if already imported
            existing = db.get_activity_by_hash(activity.fit_file_hash)
            if existing:
                skipped += 1
                continue

            # Insert activity
            activity_id = db.insert_activity(activity)

            # Calculate TSS and efficiency metrics
            tss, method, intensity_factor = calculate_tss(activity, profile)
            ef = calculate_efficiency_factor(activity)
            vi = calculate_variability_index(activity)

            # Store activity metrics
            metrics = ActivityMetrics(
                activity_id=activity_id,
                tss=tss,
                tss_method=method.value,
                intensity_factor=intensity_factor,
                efficiency_factor=ef,
                variability_index=vi,
            )
            db.insert_activity_metrics(metrics)

            imported += 1

        except Exception as e:
            print(f"Error processing {fit_file.name}: {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"Import complete!")
    print(f"  Imported: {imported}")
    print(f"  Skipped (already exists): {skipped}")
    print(f"  Failed: {failed}")
    print("=" * 60)

    # Calculate training load metrics
    if imported > 0:
        print("\nCalculating training load metrics...")

        # Get daily TSS series
        daily_tss = db.get_daily_tss_series()

        if daily_tss:
            print(f"Processing {len(daily_tss)} days of data...")

            # Calculate CTL/ATL/TSB
            training_load = calculate_training_load(daily_tss)

            # Store daily metrics
            for metrics in training_load:
                # Get activity counts for this day
                activities = db.get_activities_for_date(metrics.date)
                metrics.activity_count = len(activities)
                metrics.total_duration_s = sum(a.duration_seconds for a in activities)
                metrics.total_distance_m = sum(a.distance_meters or 0 for a in activities)

                db.upsert_daily_metrics(metrics)

            print(f"Training load calculated for {len(training_load)} days")

            # Show current form
            latest = db.get_latest_daily_metrics()
            if latest:
                print()
                print("Current Training Status:")
                print(f"  CTL (Fitness): {latest.ctl:.1f}")
                print(f"  ATL (Fatigue): {latest.atl:.1f}")
                print(f"  TSB (Form): {latest.tsb:+.1f}")
                print(f"  7-day TSS: {latest.tss_7day:.0f}")
                print(f"  30-day TSS: {latest.tss_30day:.0f}")
                if latest.acwr is not None:
                    print(f"  ACWR: {latest.acwr:.2f}")
                if latest.monotony is not None:
                    print(f"  Monotony: {latest.monotony:.2f}")
                if latest.strain is not None:
                    print(f"  Strain: {latest.strain:.0f}")

    db.close()
    print("\nDone!")


def recalculate_np():
    """Recalculate normalized power for activities that have avg_power but no NP."""
    from fitparse import FitFile

    print("=" * 60)
    print("Trainy - Recalculate Normalized Power")
    print("=" * 60)

    db = Repository(settings.database_path)

    # Get all activities with power but no NP
    all_activities = db.get_all_activities()
    activities_to_update = [
        a for a in all_activities
        if a.avg_power and not a.normalized_power and a.fit_file_path
    ]

    print(f"Found {len(activities_to_update)} activities needing NP calculation")

    updated = 0
    failed = 0

    for activity in activities_to_update:
        try:
            fit_path = Path(activity.fit_file_path)
            if not fit_path.exists():
                print(f"  File not found: {fit_path}")
                failed += 1
                continue

            # Extract power samples from FIT file
            fit = FitFile(str(fit_path))
            power_samples = []

            for record in fit.get_messages("record"):
                for field in record.fields:
                    if field.name == "power" and field.value is not None:
                        power_samples.append(field.value)
                        break

            if power_samples:
                np_value = calculate_normalized_power(power_samples)
                if np_value:
                    # Update in database
                    db.conn.execute(
                        "UPDATE activities SET normalized_power = ? WHERE id = ?",
                        (np_value, activity.id)
                    )
                    db.conn.commit()
                    print(f"  {activity.title}: NP = {np_value} W (avg = {activity.avg_power} W)")
                    updated += 1
                else:
                    failed += 1
            else:
                failed += 1

        except Exception as e:
            print(f"  Error processing {activity.title}: {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"Recalculation complete!")
    print(f"  Updated: {updated}")
    print(f"  Failed: {failed}")
    print("=" * 60)

    db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--recalculate-np":
        recalculate_np()
    else:
        main()
