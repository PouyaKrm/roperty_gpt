from typing import List
from datetime import datetime, timezone
import re
import hashlib


def compute_idempotency_key(partner: str, external_id: str, event_time_iso: str) -> str:
   
    raw = f"{partner}:{external_id}:{event_time_iso}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def normalize_address(address: str) -> str:
    return (
        address.strip().lower()
        .replace("t1", "tower 1")
        .replace("blvd", "boulevard")
        .replace("boul.", "boulevard")
        .replace("jbr", "jumeirah beach residence")
    )


def compute_dedupe_id(address: str, lat: float, lng: float) -> str:
    normalized = normalize_address(address)
    key = f"{normalized}:{round(lat, 4)}:{round(lng, 4)}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def to_iso_utc(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc)


