from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    """Pushes live occupancy updates to apps watching a location."""

    def __init__(self):
        self._subs: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, location_id: int, ws: WebSocket):
        await ws.accept()
        self._subs[location_id].add(ws)

    def disconnect(self, location_id: int, ws: WebSocket):
        self._subs[location_id].discard(ws)

    async def broadcast(self, location_id: int, payload: dict):
        for ws in list(self._subs[location_id]):
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect(location_id, ws)


manager = ConnectionManager()
