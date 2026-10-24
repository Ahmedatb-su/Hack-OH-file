import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    id_hash_secret: str
    admin_api_key: str
    reader_api_keys: frozenset
    stale_minutes_bus: int
    stale_minutes_food_court: int


def get_settings() -> Settings:
    """Read settings from the environment (cheap, so tests can override env vars)."""
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./queue.db"),
        id_hash_secret=os.getenv("ID_HASH_SECRET", "change-me"),
        admin_api_key=os.getenv("ADMIN_API_KEY", "change-me-admin"),
        reader_api_keys=frozenset(
            k.strip() for k in os.getenv("READER_API_KEYS", "reader-key-1").split(",") if k.strip()
        ),
        stale_minutes_bus=int(os.getenv("STALE_MINUTES_BUS", "90")),
        stale_minutes_food_court=int(os.getenv("STALE_MINUTES_FOOD_COURT", "120")),
    )
