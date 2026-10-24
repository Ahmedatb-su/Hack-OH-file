from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import utcnow
from ..models import Location, OccupancySnapshot, Presence, SwipeEvent
from ..schemas import ForecastOut, ForecastPoint, OccupancyOut
from ..security import hash_student_id


def level_for(percent: float) -> str:
    if percent < 40:
        return "low"
    if percent < 70:
        return "moderate"
    if percent < 95:
        return "busy"
    return "full"


def _stale_cutoff(kind: str, now: datetime) -> datetime:
    s = get_settings()
    minutes = s.stale_minutes_bus if kind == "bus" else s.stale_minutes_food_court
    return now - timedelta(minutes=minutes)


def expire_stale(db: Session, now: datetime) -> set[int]:
    """Remove people who never tapped out (left the bus/food court without swiping)."""
    touched: set[int] = set()
    rows = db.execute(select(Presence, Location).join(Location, Location.id == Presence.location_id)).all()
    for presence, loc in rows:
        if presence.last_seen < _stale_cutoff(loc.kind, now):
            db.add(SwipeEvent(location_id=loc.id, student_hash=presence.student_hash,
                              action="expired", timestamp=now))
            db.delete(presence)
            touched.add(loc.id)
    db.flush()
    for lid in touched:
        _snapshot(db, lid, now)
    return touched


def _count(db: Session, location_id: int) -> int:
    return db.scalar(select(func.count(Presence.id)).where(Presence.location_id == location_id)) or 0


def _snapshot(db: Session, location_id: int, now: datetime) -> None:
    db.add(OccupancySnapshot(location_id=location_id, count=_count(db, location_id), recorded_at=now))


def get_occupancy(db: Session, loc: Location, now: datetime | None = None) -> OccupancyOut:
    now = now or utcnow()
    count = _count(db, loc.id)
    pct = round(count / loc.capacity * 100, 1)
    return OccupancyOut(location_id=loc.id, name=loc.name, kind=loc.kind, count=count,
                        capacity=loc.capacity, percent_full=pct, level=level_for(pct), updated_at=now)


def process_swipe(db: Session, location_id: int, buck_id: str, direction: str,
                  now: datetime | None = None) -> tuple[str, bool, OccupancyOut]:
    now = now or utcnow()
    loc = db.get(Location, location_id)
    if loc is None:
        raise LookupError(f"Location {location_id} not found")

    expire_stale(db, now)
    h = hash_student_id(buck_id)
    existing = db.scalar(select(Presence).where(Presence.student_hash == h))
    here = existing is not None and existing.location_id == location_id
    touched = {location_id}

    if direction == "toggle":
        direction = "out" if here else "in"

    if direction == "out":
        if here:
            db.delete(existing)
            db.add(SwipeEvent(location_id=location_id, student_hash=h, action="out", timestamp=now))
            action = "out"
        else:
            action = "ignored"
    else:  # "in"
        if here:
            existing.last_seen = now  # duplicate tap-in: just refresh
        else:
            if existing is not None:  # still "inside" somewhere else -> auto check-out
                touched.add(existing.location_id)
                db.add(SwipeEvent(location_id=existing.location_id, student_hash=h,
                                  action="auto_checkout", timestamp=now))
                db.delete(existing)
                db.flush()
            db.add(Presence(location_id=location_id, student_hash=h, entered_at=now, last_seen=now))
            db.add(SwipeEvent(location_id=location_id, student_hash=h, action="in", timestamp=now))
        action = "in"

    db.flush()
    if action != "ignored":
        for lid in touched:
            _snapshot(db, lid, now)
    db.commit()

    occ = get_occupancy(db, loc, now)
    return action, occ.count > loc.capacity, occ


def forecast(db: Session, loc: Location, hours: int = 12, weeks: int = 4,
             now: datetime | None = None) -> ForecastOut:
    """Average historical occupancy for the same weekday + hour over the last N weeks."""
    now = now or utcnow()
    since = now - timedelta(weeks=weeks)
    snaps = db.scalars(
        select(OccupancySnapshot).where(OccupancySnapshot.location_id == loc.id,
                                        OccupancySnapshot.recorded_at >= since)
    ).all()
    buckets: dict[tuple[int, int], list[int]] = defaultdict(list)
    for s in snaps:
        buckets[(s.recorded_at.weekday(), s.recorded_at.hour)].append(s.count)

    start = now.replace(minute=0, second=0, microsecond=0)
    points = []
    for i in range(hours):
        t = start + timedelta(hours=i)
        vals = buckets.get((t.weekday(), t.hour), [])
        if vals:
            avg = sum(vals) / len(vals)
            pct = round(avg / loc.capacity * 100, 1)
            points.append(ForecastPoint(hour_start=t, expected_count=round(avg, 1),
                                        expected_percent_full=pct, level=level_for(pct),
                                        samples=len(vals)))
        else:
            points.append(ForecastPoint(hour_start=t, expected_count=None,
                                        expected_percent_full=None, level=None, samples=0))
    return ForecastOut(location_id=loc.id, name=loc.name, based_on_weeks=weeks, points=points)
