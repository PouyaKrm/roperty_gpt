from typing import List
from partners.models import Listing, Partner, PartnerAListing, PartnerBListing
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


def to_listing_from_a(a: PartnerAListing) -> Listing:
    event_time = to_iso_utc(a.updated)

    dedupe_id = compute_dedupe_id(a.address, a.lat, a.lon)

    return Listing(
        dedupe_id=dedupe_id,
        address=a.address.strip(),
        lat=a.lat,
        lng=a.lon,
        price=a.price_aed,
        beds=a.beds,
        baths=a.baths,
        status=a.status.lower(),
        updated_at=event_time,
        sources=[f"A:{a.id}"],
        version=1,
    )



def to_listing_from_b(b: PartnerBListing) -> Listing:
    event_time = to_iso_utc(b.ts)
    lat, lng = b.location["lat"], b.location["lon"]

    dedupe_id = compute_dedupe_id(b.addr, lat, lng)

    price_aed = b.price_fils // 100

    state_map = {
        "active": "for_sale",
        "inactive": "off_market",
        "sold": "sold",
    }
    status = state_map.get(b.state.lower(), "off_market")

    return Listing(
        dedupe_id=dedupe_id,
        address=b.addr.strip(),
        lat=lat,
        lng=lng,
        price=price_aed,
        beds=b.br,
        baths=b.ba,
        status=status,
        updated_at=event_time,
        sources=[f"B:{b.ext_id}"],
        version=1,
    )


