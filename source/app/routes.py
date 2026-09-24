"""HTTP endpoints for the address book API."""

import logging

from fastapi import APIRouter, HTTPException, Query, status

from app.schema import (
    AddressCreate,
    AddressOut,
    AddressUpdate,
    AddressWithDistance,
)
from app.service import address_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.post(
    "",
    response_model=AddressOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new address",
)
def create_address(data: AddressCreate) -> AddressOut:
    """Create a new address with validated coordinates."""
    address = address_service.create(data)
    return AddressOut.model_validate(address)


@router.get(
    "",
    response_model=list[AddressOut],
    summary="List addresses (paginated)",
)
def list_addresses(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[AddressOut]:
    """Return addresses ordered by id with limit/offset pagination."""
    addresses = address_service.list(limit=limit, offset=offset)
    return [AddressOut.model_validate(a) for a in addresses]


@router.get(
    "/nearby",
    response_model=list[AddressWithDistance],
    summary="Find addresses within a radius",
)
def get_nearby_addresses(
    lat: float = Query(..., ge=-90, le=90, description="Origin latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Origin longitude"),
    radius_km: float = Query(..., gt=0, le=20000, description="Search radius in km"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[AddressWithDistance]:
    """Return addresses within radius_km of (lat, lon), sorted by distance."""
    hits = address_service.find_nearby(
        lat=lat, lon=lon, radius_km=radius_km, limit=limit, offset=offset
    )
    return [
        AddressWithDistance(
            **AddressOut.model_validate(address).model_dump(),
            distance_km=distance,
        )
        for address, distance in hits
    ]


@router.get(
    "/{address_id}",
    response_model=AddressOut,
    summary="Get one address",
)
def get_address(address_id: int) -> AddressOut:
    """Fetch a single address by id (404 if missing)."""
    address = address_service.get(address_id)
    if address is None:
        logger.warning("GET address id=%s not found", address_id)
        raise HTTPException(status_code=404, detail="Address not found")
    return AddressOut.model_validate(address)


@router.put(
    "/{address_id}",
    response_model=AddressOut,
    summary="Update an address",
)
def update_address(address_id: int, data: AddressUpdate) -> AddressOut:
    """Fully update an address (404 if missing)."""
    address = address_service.update(address_id, data)
    if address is None:
        logger.warning("PUT address id=%s not found", address_id)
        raise HTTPException(status_code=404, detail="Address not found")
    return AddressOut.model_validate(address)


@router.delete(
    "/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an address",
)
def delete_address(address_id: int) -> None:
    """Delete an address (404 if missing)."""
    if not address_service.delete(address_id):
        logger.warning("DELETE address id=%s not found", address_id)
        raise HTTPException(status_code=404, detail="Address not found")
