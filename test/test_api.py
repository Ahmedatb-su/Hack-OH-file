from datetime import timedelta

from app.database import SessionLocal, utcnow
from app.models import Location, Presence
from app.services.occupancy import expire_stale, forecast

R = {"X-API-Key": "reader"}


def swipe(client, loc, buck, direction="toggle"):
    return client.post("/swipes", json={"location_id": loc, "buck_id": buck, "direction": direction}, headers=R)


def test_auth_required(client, bus):
    assert client.post("/swipes", json={"location_id": bus, "buck_id": "abc123"}).status_code == 401
    assert client.post("/locations", json={"name": "x", "kind": "bus", "capacity": 5}).status_code == 401


def test_toggle_in_and_out(client, bus):
    r = swipe(client, bus, "buck.1").json()
    assert r["action"] == "in" and r["occupancy"]["count"] == 1
    r = swipe(client, bus, "buck.1").json()
    assert r["action"] == "out" and r["occupancy"]["count"] == 0


def test_moving_locations_auto_checks_out(client, bus):
    other = client.post("/locations", json={"name": "Union", "kind": "food_court", "capacity": 100},
                        headers={"X-API-Key": "admin"}).json()["location_id"]
    swipe(client, bus, "buck.2")
    swipe(client, other, "buck.2")
    assert client.get(f"/locations/{bus}/occupancy").json()["count"] == 0
    assert client.get(f"/locations/{other}/occupancy").json()["count"] == 1


def test_levels_and_over_capacity(client, bus):
    for i in range(10):
        swipe(client, bus, f"buck.{i}")
    occ = client.get(f"/locations/{bus}/occupancy").json()
    assert occ["level"] == "full" and occ["percent_full"] == 100.0
    assert swipe(client, bus, "buck.99").json()["over_capacity"] is True


def test_raw_id_never_stored(client, bus):
    swipe(client, bus, "buck.secret")
    with SessionLocal() as db:
        assert "buck.secret" not in [p.student_hash for p in db.query(Presence)]


def test_stale_presence_expires(client, bus):
    swipe(client, bus, "buck.3")
    with SessionLocal() as db:
        expire_stale(db, utcnow() + timedelta(hours=3))
        db.commit()
    assert client.get(f"/locations/{bus}/occupancy").json()["count"] == 0


def test_forecast_uses_history(client, bus):
    swipe(client, bus, "buck.4")
    with SessionLocal() as db:
        loc = db.get(Location, bus)
        f = forecast(db, loc, hours=1)
    assert f.points[0].expected_count is not None and f.points[0].samples >= 1


def test_unknown_location(client):
    assert swipe(client, 999, "buck.5").status_code == 404
