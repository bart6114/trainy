"""Metrics API schemas."""

from datetime import date
from typing import Optional
from pydantic import BaseModel, computed_field


class CurrentMetricsResponse(BaseModel):
    """Current training metrics (CTL/ATL/TSB)."""

    date: date
    ctl: float
    atl: float
    tsb: float
    tss_7day: Optional[float] = None
    tss_30day: Optional[float] = None
    tss_90day: Optional[float] = None

    # New advanced metrics
    acwr: Optional[float] = None  # Acute:Chronic Workload Ratio
    monotony: Optional[float] = None  # Training monotony
    strain: Optional[float] = None  # Training strain

    @computed_field
    @property
    def form_status(self) -> str:
        """Get form status based on TSB."""
        if self.tsb > 25:
            return "Transition"
        elif self.tsb > 5:
            return "Fresh"
        elif self.tsb > -10:
            return "Neutral"
        elif self.tsb > -30:
            return "Tired"
        else:
            return "Exhausted"

    @computed_field
    @property
    def form_color(self) -> str:
        """Get form status color."""
        if self.tsb > 25:
            return "yellow"
        elif self.tsb > 5:
            return "green"
        elif self.tsb > -10:
            return "blue"
        elif self.tsb > -30:
            return "orange"
        else:
            return "red"

    @computed_field
    @property
    def acwr_status(self) -> str:
        """Get ACWR risk status."""
        if self.acwr is None:
            return "Unknown"
        elif self.acwr < 0.8:
            return "Undertrained"
        elif self.acwr <= 1.3:
            return "Optimal"
        elif self.acwr <= 1.5:
            return "Caution"
        else:
            return "Danger"

    @computed_field
    @property
    def acwr_color(self) -> str:
        """Get ACWR status color."""
        if self.acwr is None:
            return "gray"
        elif self.acwr < 0.8:
            return "yellow"
        elif self.acwr <= 1.3:
            return "green"
        elif self.acwr <= 1.5:
            return "orange"
        else:
            return "red"


class DailyMetricsItem(BaseModel):
    """Single day's metrics."""

    date: date
    total_tss: float
    activity_count: int
    total_duration_s: float
    total_distance_m: float
    ctl: Optional[float] = None
    atl: Optional[float] = None
    tsb: Optional[float] = None
    acwr: Optional[float] = None
    monotony: Optional[float] = None
    strain: Optional[float] = None


class DailyMetricsResponse(BaseModel):
    """Daily metrics for a date range."""

    start_date: date
    end_date: date
    items: list[DailyMetricsItem]


class WeeklyTSSItem(BaseModel):
    """Weekly TSS total."""

    week_start: date
    week_end: date
    total_tss: float
    activity_count: int


class WeeklyTSSResponse(BaseModel):
    """Weekly TSS totals."""

    weeks: int
    items: list[WeeklyTSSItem]
