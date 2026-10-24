from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..realtime import manager
from ..schemas import SwipeIn, SwipeOut
from ..security import require_reader
from ..services.occupancy import process_swipe

router = APIRouter(prefix="/swipes", tags=["swipes"])


@router.post("", response_model=SwipeOut, dependencies=[Depends(require_reader)])
def swipe(payload: SwipeIn, background: BackgroundTasks, db: Session = Depends(get_db)):
    """Called by a card reader when a Buck ID is swiped."""
    try:
        action, over, occ = process_swipe(db, payload.location_id, payload.buck_id, payload.direction)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    background.add_task(manager.broadcast, occ.location_id, occ.model_dump(mode="json"))
    return SwipeOut(action=action, over_capacity=over, occupancy=occ)
