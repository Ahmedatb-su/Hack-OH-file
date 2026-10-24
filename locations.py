from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db, utcnow
from ..models import Location
from ..realtime import manager
from ..schemas import ForecastOut, LocationCreate, OccupancyOut
from ..security import require_admin
from ..services.occupancy import expire_stale, forecast, get_occupancy

router = APIRouter(prefix="/locations", tags=["locations"])


def _get_or_404(db: Session, location_id: int) -> Location:
    loc = db.get(Location, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc


@router.post("", response_model=OccupancyOut, status_code=201, dependencies=[Depends(require_admin)])
def create_location(payload: LocationCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Location).where(Location.name == payload.name)):
        raise HTTPException(status_code=409, detail="Location name already exists")
    loc = Location(**payload.model_dump())
    db.add(loc)
    db.commit()
    return get_occupancy(db, loc)


@router.get("", response_model=list[OccupancyOut])
def list_locations(kind: str | None = Query(default=None, pattern="^(bus|food_court)$"),
                   db: Session = Depends(get_db)):
    expire_stale(db, utcnow())
    db.commit()
    q = select(Location).order_by(Location.name)
    if kind:
        q = q.where(Location.kind == kind)
    return [get_occupancy(db, loc) for loc in db.scalars(q)]


@router.get("/{location_id}/occupancy", response_model=OccupancyOut)
def occupancy(location_id: int, db: Session = Depends(get_db)):
    loc = _get_or_404(db, location_id)
    expire_stale(db, utcnow())
    db.commit()
    return get_occupancy(db, loc)


@router.get("/{location_id}/forecast", response_model=ForecastOut)
def location_forecast(location_id: int, hours: int = Query(12, ge=1, le=48),
                      weeks: int = Query(4, ge=1, le=12), db: Session = Depends(get_db)):
    return forecast(db, _get_or_404(db, location_id), hours=hours, weeks=weeks)


@router.websocket("/{location_id}/live")
async def live(location_id: int, ws: WebSocket):
    """Subscribe to live occupancy pushes for one bus / food court."""
    await manager.connect(location_id, ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive; clients needn't send anything
    except WebSocketDisconnect:
        manager.disconnect(location_id, ws)
