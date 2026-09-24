"""Application entrypoint: wires logging, routes and database creation."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.logging_config import setup_logging
from app.models import Address  # noqa: F401
from app.routes import router as addresses_router

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Address Book API", lifespan=lifespan)
app.include_router(addresses_router)
