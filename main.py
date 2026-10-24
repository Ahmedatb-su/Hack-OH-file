from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import Base, engine
from .routers import locations, swipes


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)  # swap for Alembic migrations in production
    yield


app = FastAPI(title="BuckeyeQueue API",
              description="Live crowd levels for buses and food courts, driven by Buck ID swipes.",
              version="0.1.0", lifespan=lifespan)
app.include_router(swipes.router)
app.include_router(locations.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
