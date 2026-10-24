from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class LocationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    kind: Literal["bus", "food_court"]
    capacity: int = Field(gt=0, le=5000)


class OccupancyOut(BaseModel):
    location_id: int
    name: str
    kind: str
    count: int
    capacity: int
    percent_full: float
    level: Literal["low", "moderate", "busy", "full"]
    updated_at: datetime


class SwipeIn(BaseModel):
    location_id: int
    buck_id: str = Field(min_length=3, max_length=32)
    # "toggle": first swipe = in, second = out. Buses with only a boarding reader can use "in".
    direction: Literal["toggle", "in", "out"] = "toggle"


class SwipeOut(BaseModel):
    action: Literal["in", "out", "ignored"]
    over_capacity: bool
    occupancy: OccupancyOut


class ForecastPoint(BaseModel):
    hour_start: datetime
    expected_count: Optional[float]
    expected_percent_full: Optional[float]
    level: Optional[str]
    samples: int


class ForecastOut(BaseModel):
    location_id: int
    name: str
    based_on_weeks: int
    points: list[ForecastPoint]
