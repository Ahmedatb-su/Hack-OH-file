import os
import tempfile

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
os.environ["ID_HASH_SECRET"] = "test-secret"
os.environ["ADMIN_API_KEY"] = "admin"
os.environ["READER_API_KEYS"] = "reader"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def bus(client):
    r = client.post("/locations", json={"name": "Bus 1", "kind": "bus", "capacity": 10},
                    headers={"X-API-Key": "admin"})
    return r.json()["location_id"]
