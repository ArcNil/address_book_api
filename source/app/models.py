"""SQLAlchemy ORM models for persisted address records."""

from datetime import datetime, timezone

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now():
    """Returns the current UTC time for timestamp defaults."""
    return datetime.now(timezone.utc)


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    address_text: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now)
