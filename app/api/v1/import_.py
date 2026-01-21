"""Import API endpoints with SSE streaming."""

import asyncio
import json
import re
from datetime import datetime, date
from typing import AsyncIterator

from fastapi import APIRouter, Depends, Query
from sse_starlette.sse import EventSourceResponse

from trainy.database import Repository
from trainy.importers.fit_importer import FitImporter, parse_fit_file
from trainy.metrics.tss import calculate_tss
from trainy.adherence import AdherenceTracker
from trainy.config import settings
from app.dependencies import get_repo

router = APIRouter()

# Pattern to extract date from filename like "2014-12-28_11-01-24_pf_42039501.fit"
FILENAME_DATE_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})_")


def extract_date_from_filename(filename: str) -> date | None:
    """Extract date from FIT filename if it matches the expected pattern."""
    match = FILENAME_DATE_PATTERN.match(filename)
    if match:
        try:
            return date.fromisoformat(match.group(1))
        except ValueError:
            return None
    return None


async def import_generator(
    from_date: date | None,
    repo: Repository,
) -> AsyncIterator[dict]:
    """Generate SSE events for import progress."""
    importer = FitImporter(settings.rungap_path)
    fit_files = list(importer.get_fit_files())
    total = len(fit_files)

    if total == 0:
        yield {
            "event": "complete",
            "data": json.dumps({"imported": 0, "skipped": 0, "errors": 0, "total": 0}),
        }
        return

    yield {
        "event": "start",
        "data": json.dumps({"total": total}),
    }
    await asyncio.sleep(0)

    imported = 0
    skipped = 0
    errors = 0
    profile = repo.get_current_profile()

    for i, fit_path in enumerate(fit_files, 1):
        try:
            # Quick filter by filename date (before expensive parsing)
            if from_date:
                file_date = extract_date_from_filename(fit_path.name)
                if file_date and file_date < from_date:
                    skipped += 1
                    yield {
                        "event": "skip",
                        "data": json.dumps({
                            "file": fit_path.name,
                            "reason": "Before filter date",
                            "progress": i,
                            "total": total,
                        }),
                    }
                    await asyncio.sleep(0)
                    continue

            # Parse FIT file
            print(f"Processing: {fit_path.name}")
            activity = parse_fit_file(fit_path, include_raw_data=True)

            if not activity:
                print(f"  -> ERROR: Failed to parse")
                errors += 1
                yield {
                    "event": "error",
                    "data": json.dumps({"file": fit_path.name, "error": "Failed to parse"}),
                }
                await asyncio.sleep(0)
                continue

            # Check date filter
            if from_date and activity.start_time.date() < from_date:
                print(f"  -> SKIP: Before filter date ({activity.start_time.date()} < {from_date})")
                skipped += 1
                yield {
                    "event": "skip",
                    "data": json.dumps({
                        "file": fit_path.name,
                        "reason": "Before filter date",
                        "progress": i,
                        "total": total,
                    }),
                }
                await asyncio.sleep(0)
                continue

            # Check if already imported
            existing = repo.get_activity_by_hash(activity.fit_file_hash)
            if existing:
                print(f"  -> SKIP: Already imported")
                skipped += 1
                yield {
                    "event": "skip",
                    "data": json.dumps({
                        "file": fit_path.name,
                        "reason": "Already imported",
                        "progress": i,
                        "total": total,
                    }),
                }
                await asyncio.sleep(0)
                continue

            # Insert activity
            print(f"  -> IMPORTED: {activity.activity_type} on {activity.start_time.date()}")
            activity_id = repo.insert_activity(activity)

            # Calculate TSS
            tss, method, intensity_factor = calculate_tss(activity, profile, activity.raw_fit_data)
            if tss:
                repo.update_activity_tss(activity_id, tss, str(method), intensity_factor)

            # Try to match with planned workouts for the same date
            tracker = AdherenceTracker(repo)
            tracker.reconcile_date(activity.start_time.date())

            imported += 1
            yield {
                "event": "import",
                "data": json.dumps({
                    "file": fit_path.name,
                    "activity_type": activity.activity_type,
                    "date": activity.start_time.isoformat(),
                    "tss": round(tss, 1) if tss else None,
                    "progress": i,
                    "total": total,
                }),
            }
            await asyncio.sleep(0)

        except Exception as e:
            errors += 1
            yield {
                "event": "error",
                "data": json.dumps({"file": fit_path.name, "error": str(e)}),
            }
            await asyncio.sleep(0)

    # Mark metrics as dirty after import
    if imported > 0:
        repo.set_metrics_dirty(True)

    yield {
        "event": "complete",
        "data": json.dumps({
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
            "total": total,
        }),
    }


@router.get("/stream")
async def import_stream(
    from_date: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    repo: Repository = Depends(get_repo),
):
    """Stream import progress via SSE."""
    parsed_date = date.fromisoformat(from_date) if from_date else None
    return EventSourceResponse(import_generator(parsed_date, repo))


@router.get("/status")
async def import_status(
    repo: Repository = Depends(get_repo),
):
    """Get import status and available files."""
    if not settings.rungap_exists:
        return {
            "available": False,
            "file_count": 0,
            "message": "RunGap directory not found",
        }

    importer = FitImporter(settings.rungap_path)
    file_count = importer.count_files()

    return {
        "available": True,
        "file_count": file_count,
        "message": f"{file_count} FIT files available for import",
    }
