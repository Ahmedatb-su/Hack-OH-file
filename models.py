from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base, utcnow


class Location(Base):
    """A bus (e.g. a COTA route/vehicle) or a food court."""

    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    kind: Mapped[str] = mapped_column(String(20))  # "bus" | "food_court"
    capacity: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Presence(Base):
    """Who is currently inside a location. One row per student, max."""

    __tablename__ = "presence"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    student_hash: Mapped[str] = mapped_column(String(64), unique=True)
    entered_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SwipeEvent(Base):
    """Append-only audit log of every state change."""

    __tablename__ = "swipe_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    student_hash: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(20))  # in | out | auto_checkout | expired
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class OccupancySnapshot(Base):
    """Occupancy count after each change; powers the crowd forecast."""

    __tablename__ = "occupancy_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))
    count: Mapped[int] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    __table_args__ = (Index("ix_snap_loc_time", "location_id", "recorded_at"),)
