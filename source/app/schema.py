"""Pydantic schemas for request validation and response serialization."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AddressBase(BaseModel):
    """Shared fields for creating/updating an address."""

    address_text: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Street address or label (non-empty, max 255 chars).",
    )
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees.")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees.")


class AddressCreate(AddressBase):
    """Payload for POST /addresses."""


class AddressUpdate(AddressBase):
    """Payload for PUT /addresses/{id} (full update)."""


class AddressOut(AddressBase):
    """Address as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class AddressWithDistance(AddressOut):
    """Address plus computed distance from the search origin (km)."""

    distance_km: float


class NearbySearchParams(BaseModel):
    """Query parameters for GET /addresses/nearby."""

    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(..., gt=0, le=20000, description="Search radius in km.")
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)