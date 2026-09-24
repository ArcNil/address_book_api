"""Application entrypoint: wires logging, routes and database creation."""

from fastapi import FastAPI

from app.database import Base, engine
from app.logging_config import setup_logging
from app.models import Address  # noqa: F401
from app.routes import router as addresses_router

setup_logging()

app = FastAPI(title="Address Book API")
app.include_router(addresses_router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
