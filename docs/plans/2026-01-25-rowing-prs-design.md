# Rowing PRs Analytics Tab Design

## Overview
Add a new "Rowing PRs" tab to the Analytics page showing peak rowing performances across standard distances and time durations.

## Benchmarks

**Distance PRs** (best time):
- 500m, 1000m, 2000m, 5000m, 10000m

**Time-based Power PRs** (best average power):
- 1min, 4min, 30min, 60min

## Data Model

### Distance PRs
- Query activities where `activity_type='row'` and `distance_meters` matches target (±2% tolerance)
- Best = lowest `duration_seconds` for each distance
- Display as split time (per 500m) and total time

### Time-based PRs
- Parse `raw_fit_data` blob (gzip JSON) to extract power samples
- Use `calculate_peak_power()` with windows: 60s, 240s, 1800s, 3600s
- Extend `activity_metrics` with new columns: `peak_power_4min`, `peak_power_30min`, `peak_power_60min`

## UI Layout

New tab "Rowing PRs" in Analytics page:

```
┌─────────────────────────────────────────────────────────┐
│  Distance PRs                                           │
│  ┌─────────┬─────────┬─────────┬─────────┬───────────┐  │
│  │  500m   │  1000m  │  2000m  │  5000m  │  10000m   │  │
│  │  1:32.5 │  3:12.4 │  6:45.2 │  17:42  │  36:15    │  │
│  │  1:32/5 │  1:36/5 │  1:41/5 │  1:46/5 │  1:49/5   │  │
│  │  Dec 24 │  Jan 5  │    -    │  Jan 7  │  Jan 22   │  │
│  └─────────┴─────────┴─────────┴─────────┴───────────┘  │
│                                                         │
│  Power PRs                                              │
│  ┌─────────┬─────────┬─────────┬─────────┐              │
│  │  1 min  │  4 min  │  30 min │  60 min │              │
│  │  285 W  │  245 W  │  195 W  │  175 W  │              │
│  │  Jan 14 │  Dec 22 │  Jan 5  │    -    │              │
│  └─────────┴─────────┴─────────┴─────────┘              │
└─────────────────────────────────────────────────────────┘
```

Each card shows:
- Total time (distance) or watts (power)
- Split pace per 500m (distance PRs only)
- Date achieved
- Missing PRs show "-" with muted styling
