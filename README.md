# BuckeyeQueue (backend)

Live crowd levels for campus buses (COTA/CABS) and food courts, driven by Buck ID swipes.
Card readers report swipes → the API tracks who is inside each location → students see
exactly how packed a bus or food court is, plus a forecast for the next few hours.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then edit the secrets
export $(grep -v '^#' .env | xargs)
python -m scripts.seed          # demo buses + food courts
uvicorn app.main:app --reload
```

Interactive docs: http://localhost:8000/docs  ·  Tests: `pytest`  ·  Docker: `docker build -t buckeye-queue . && docker run -p 8000:8000 --env-file .env buckeye-queue`

## How it works

| Swipe | Result |
|---|---|
| First swipe at a location | Student is added to that location's count |
| Second swipe at the same location | Student is removed (tap-out) |
| Swipe at a different location | Auto-removed from the old one, added to the new one |
| Never tapped out | Auto-expired after `STALE_MINUTES_*` so counts self-correct |

Buses with only a boarding reader can send `"direction": "in"`; stale expiry handles exits.
Occupancy levels: `low` <40%, `moderate` <70%, `busy` <95%, `full` ≥95% of capacity.

## API

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/swipes` | `X-API-Key` (reader) | Report a swipe `{location_id, buck_id, direction}` |
| GET | `/locations?kind=bus\|food_court` | none | All locations with live counts |
| GET | `/locations/{id}/occupancy` | none | Count, % full, level |
| GET | `/locations/{id}/forecast?hours=12&weeks=4` | none | Expected crowd by hour (same weekday/hour history) |
| POST | `/locations` | `X-API-Key` (admin) | Create a bus / food court |
| WS | `/locations/{id}/live` | none | Live push on every change |

```bash
curl -X POST localhost:8000/swipes -H "X-API-Key: reader-key-1" -H "Content-Type: application/json" \
  -d '{"location_id": 1, "buck_id": "buckeye.1"}'
```

## Privacy

- Buck IDs are **HMAC-SHA256 hashed** with `ID_HASH_SECRET` immediately; raw IDs are never stored or logged.
- Public endpoints only expose aggregate counts, never who is where.
- Before deploying on a real campus: get approval from the university (OSU IT / Transportation & Traffic Management / COTA), review FERPA/data-retention requirements, and consider purging `swipe_events` after a short window.

## Layout

```
app/
  main.py            FastAPI app
  models.py          Location, Presence, SwipeEvent, OccupancySnapshot
  services/occupancy.py   swipe logic, expiry, levels, forecast
  routers/           /swipes, /locations (+ websocket)
  security.py        ID hashing, API-key auth
scripts/seed.py      demo data
tests/               pytest suite
```

## Next steps

- Postgres (`DATABASE_URL=postgresql+psycopg://...`) + Alembic migrations
- Redis pub/sub so websocket broadcasts work across multiple workers
- Per-reader keys mapped to a fixed `location_id` (so a reader can't report for another location)
- Time-weighted forecast / ML model; integrate COTA GTFS-realtime for bus positions
