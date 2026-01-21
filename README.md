# Trainy - Training Tracking TUI Application

A terminal-based training/exercise tracking application built with Textual (Python TUI framework), integrating with RunGap FIT files, SQLite storage, and OpenRouter AI for training plan generation.

## Features

- **Calendar View**: Monthly calendar showing activities and planned workouts with TSS values and form status coloring
- **Activity List**: DataTable view of all activities with filtering and sorting
- **Metrics Dashboard**: Training load visualization (CTL/ATL/TSB), rolling TSS, and form status
- **Feedback System**: Log subjective workout feedback including RPE, sleep, soreness, and injury tracking
- **AI Planning**: Generate training plans using OpenRouter AI with structured output
- **Settings**: Configure thresholds (FTP, LTHR, pace) and trigger metric recalculation

## Installation

```bash
# Clone and enter directory
cd trainy

# Install dependencies with uv
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your paths and API key
```

## Configuration

Create a `.env` file with:

```bash
RUNGAP_PATH="/path/to/RunGap/Export"
OPENROUTER_API_KEY="your-key-here"  # Optional, for AI planning
DATABASE_PATH="./trainy.db"
```

## Usage

### Import Activities

Import FIT files from RunGap:

```bash
uv run python scripts/import_activities.py
```

This will:
- Parse all FIT files in your RunGap export directory
- Calculate TSS using power, HR, or pace-based methods
- Calculate CTL/ATL/TSB training load metrics

### Run the TUI

```bash
uv run trainy
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `c` | Calendar view |
| `a` | Activities list |
| `m` | Metrics dashboard |
| `p` | AI Planning |
| `s` | Settings |
| `q` | Quit |
| `?` | Show help |

### Calendar Navigation

| Key | Action |
|-----|--------|
| `←/→` | Previous/Next day |
| `↑/↓` | Previous/Next week |
| `PgUp/PgDn` | Previous/Next month |
| `Home` | Today |
| `Enter` | Select day |
| `f` | Add feedback |

## Project Structure

```
trainy/
├── trainy/
│   ├── app.py              # Main Textual App
│   ├── config.py           # Settings from .env
│   ├── static/
│   │   └── styles.tcss     # Textual CSS
│   ├── screens/
│   │   ├── calendar.py     # Calendar view
│   │   ├── activities.py   # Activity list
│   │   ├── feedback.py     # Workout feedback input
│   │   ├── planning.py     # AI training plan generation
│   │   ├── metrics.py      # Training load dashboard
│   │   └── settings.py     # User thresholds configuration
│   ├── widgets/
│   │   ├── calendar_widget.py  # Custom calendar grid
│   │   └── metrics_card.py     # TSS/CTL/ATL display
│   ├── database/
│   │   ├── models.py       # Pydantic models
│   │   ├── repository.py   # Data access layer
│   │   └── migrations.py   # Schema versioning
│   ├── importers/
│   │   └── fit_importer.py # FIT file parsing
│   ├── metrics/
│   │   ├── tss.py          # TSS calculations
│   │   └── training_load.py # CTL/ATL/TSB
│   └── ai/
│       └── openrouter.py   # AI training plan generation
└── scripts/
    └── import_activities.py # CLI for initial import
```

## Metrics

### TSS Calculation

- **Power-based** (cycling with power meter): Uses normalized power and FTP
- **Heart Rate-based**: Uses LTHR and HR reserve
- **Pace-based** (running/swimming): Uses threshold pace

### Training Load

- **CTL** (Chronic Training Load): 42-day EWMA of TSS
- **ATL** (Acute Training Load): 7-day EWMA of TSS
- **TSB** (Training Stress Balance): CTL - ATL

### Form Status

| TSB Range | Status | Description |
|-----------|--------|-------------|
| > 25 | Transition | Potentially detrained |
| 5 to 25 | Fresh | Ready to race |
| -10 to 5 | Neutral | Optimal training |
| -30 to -10 | Tired | Building fitness |
| < -30 | Exhausted | Risk of overtraining |

## Development

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run with textual dev tools
uv run textual run --dev trainy.app:TrainyApp
```

## License

MIT
