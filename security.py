import hashlib
import hmac

from fastapi import Header, HTTPException

from .config import get_settings


def hash_student_id(buck_id: str) -> str:
    """Keyed hash so raw Buck IDs are never stored and can't be rainbow-tabled."""
    secret = get_settings().id_hash_secret.encode()
    return hmac.new(secret, buck_id.strip().encode(), hashlib.sha256).hexdigest()


def require_reader(x_api_key: str = Header(default="")) -> None:
    keys = get_settings().reader_api_keys
    if not any(hmac.compare_digest(x_api_key, k) for k in keys):
        raise HTTPException(status_code=401, detail="Invalid reader API key")


def require_admin(x_api_key: str = Header(default="")) -> None:
    if not hmac.compare_digest(x_api_key, get_settings().admin_api_key):
        raise HTTPException(status_code=401, detail="Invalid admin API key")
