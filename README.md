# Address Book API

FastAPI application for managing validated addresses and finding them by
geographic distance. Addresses are stored in SQLite.

## Requirements

- Python 3.13+ (or Docker with Docker Compose)

## Run with Docker Compose (recommended)

```bash
docker compose up --build
```

The API is available at `http://127.0.0.1:8000`, and Swagger UI is available
at `http://127.0.0.1:8000/docs`.

The SQLite database (`/data/addresses.db`) and application logs
(`/tmp/app-logs/app.log`) are persisted in named Docker volumes, so data
survives container restarts. To stop:

```bash
docker compose down
```

## Run locally (without Docker)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r source/requirements.txt
uvicorn app.main:app --reload --app-dir source
```

By default the database is created at `/tmp/addresses.db` and logs are written
to `/tmp/app-logs/app.log`. Both locations can be overridden with the
`DATABASE_URL` and `APP_LOG_FILE` environment variables.

## Tests

The test suite runs inside Docker (no local Python needed):

```bash
docker compose run --rm test
```

It spins up a throwaway container, runs `pytest` against an isolated SQLite
database, and removes itself afterwards. Expected output ends with something
like `21 passed`.

## Endpoints

- `POST /addresses` — create an address
- `GET /addresses` — list addresses (supports `limit` and `offset`)
- `GET /addresses/{id}` — get one address
- `PUT /addresses/{id}` — update an address
- `DELETE /addresses/{id}` — delete an address
- `GET /addresses/nearby?lat=&lon=&radius_km=` — find addresses within a radius

The nearby search applies a SQL bounding-box pre-filter followed by an exact
Haversine calculation and returns results sorted by distance ascending.

## Notes

- `addresses.db` is created automatically on startup.
- Application logs are written to the console and to the path configured by
  `APP_LOG_FILE` (default: `/tmp/app-logs/app.log`).
- The scope of the implementation intentionally mirrors the assignment: a
  minimal, single-purpose API kept as simple as the task allows — no extra
  layers or features beyond what was asked for.
