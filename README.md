# Spectrogram Generator API

FastAPI micro‑service that converts raw audio uploads into spectrogram PNGs.

## What & Why

Built to translate my Django experience to FastAPI.

## Stack

* **Python 3.x** (tested on 3.10), managed with Poetry
* **FastAPI**
* **Celery** 
* **Redis**
* **Docker**
* **SQLite** (for now)


## Quick start

```bash
poetry install
# run db migrations
alembic upgrade head
# dev server
poetry run uvicorn app.main:app --reload
# start Redis
docker-compose up -d 
# start background worker for audio processing
poetry run celery -A app.celery_app worker  --loglevel=info
```

Open **[http://localhost:8000/docs](http://localhost:8000/docs)** for interactive Swagger.

## Tests

```bash
poetry run pytest
```

## Roadmap

* Switch from SQLite to PostgreSQL
* Replace DB blob storage with MinIO
* CI/CD: GitHub Actions + Docker‑based integration tests
* Add endpoint that allows tracking of background task status
* Return images as base64 instead of saving to disk
* Graceful handling of corrupt audio files
* Dockerize API and Celery workers
