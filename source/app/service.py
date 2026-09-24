"""Service layer for address operations.

Combines the geo math (Haversine) and all persistence/business logic in
one place. Routers call methods on the shared ``address_service`` instance
and never touch SQLAlchemy directly.
"""

from __future__ import annotations

import logging
import math

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Address
from app.schema import AddressCreate, AddressUpdate

logger = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0

# Rough km-per-degree used for the bounding-box pre-filter.
KM_PER_DEG_LAT = 111.0


def haversine_distance_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Great-circle distance between two points in kilometres (Haversine)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


class AddressService:
    """Handles all address CRUD and the nearby search.

    Each method opens its own session, so the service is stateless and
    safe to share; callers never manage sessions themselves.
    """

    def _session(self) -> Session:
        return SessionLocal()

    def create(self, data: AddressCreate) -> Address:
        """Persist a new address and return the stored row."""
        with self._session() as db:
            address = Address(
                address_text=data.address_text.strip(),
                latitude=data.latitude,
                longitude=data.longitude,
            )
            db.add(address)
            db.commit()
            db.refresh(address)
            logger.info("Created address id=%s", address.id)
            # Detach so the caller isn't tied to a closed session.
            db.expunge(address)
            return address

    def get(self, address_id: int) -> Address | None:
        """Fetch one address by id, or None if missing."""
        with self._session() as db:
            address = db.get(Address, address_id)
            if address is not None:
                db.expunge(address)
            return address

    def list(self, limit: int = 100, offset: int = 0) -> list[Address]:
        """Return addresses ordered by id, paginated."""
        with self._session() as db:
            stmt = select(Address).order_by(Address.id).limit(limit).offset(offset)
            addresses = list(db.scalars(stmt))
            for address in addresses:
                db.expunge(address)
            return addresses

    def update(self, address_id: int, data: AddressUpdate) -> Address | None:
        """Apply a full update; returns None if the address doesn't exist."""
        with self._session() as db:
            address = db.get(Address, address_id)
            if address is None:
                logger.warning("Update failed, address id=%s not found", address_id)
                return None
            address.address_text = data.address_text.strip()
            address.latitude = data.latitude
            address.longitude = data.longitude
            db.commit()
            db.refresh(address)
            logger.info("Updated address id=%s", address.id)
            db.expunge(address)
            return address

    def delete(self, address_id: int) -> bool:
        """Delete an address; returns False if it doesn't exist."""
        with self._session() as db:
            address = db.get(Address, address_id)
            if address is None:
                logger.warning("Delete failed, address id=%s not found", address_id)
                return False
            db.delete(address)
            db.commit()
            logger.info("Deleted address id=%s", address_id)
            return True

    def count(self) -> int:
        """Total number of stored addresses."""
        with self._session() as db:
            return db.scalar(select(func.count()).select_from(Address)) or 0

    def find_nearby(
        self,
        lat: float,
        lon: float,
        radius_km: float,
        limit: int = 100,
        offset: int = 0,
    ) -> list[tuple[Address, float]]:
        """Return (address, distance_km) pairs within radius, sorted by distance.

        Bounding-box SQL pre-filter, then exact Haversine in Python.
        """
        lat_delta = radius_km / KM_PER_DEG_LAT
        # Guard against degrees shrinking to zero near the poles.
        lon_delta = radius_km / max(KM_PER_DEG_LAT * math.cos(math.radians(lat)), 1e-9)

        with self._session() as db:
            stmt = (
                select(Address)
                .where(
                    Address.latitude >= lat - lat_delta,
                    Address.latitude <= lat + lat_delta,
                    Address.longitude >= lon - lon_delta,
                    Address.longitude <= lon + lon_delta,
                )
                .limit(limit * 4 + offset)  # over-fetch so post-filter fills the page
            )
            candidates = list(db.scalars(stmt))
            for address in candidates:
                db.expunge(address)

        hits: list[tuple[Address, float]] = []
        for address in candidates:
            distance = haversine_distance_km(lat, lon, address.latitude, address.longitude)
            if distance <= radius_km:
                hits.append((address, distance))

        hits.sort(key=lambda pair: pair[1])
        logger.info(
            "Nearby search lat=%s lon=%s radius_km=%s -> %d hits (%d candidates)",
            lat, lon, radius_km, len(hits[offset:offset + limit]), len(candidates),
        )
        return hits[offset:offset + limit]


# Shared instance used by the routers.
address_service = AddressService()