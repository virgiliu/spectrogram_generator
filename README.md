# Spectrogram Generator API

FastAPI micro‑service that converts raw audio uploads into spectrogram PNGs.

## What & Why

Built to translate my Django experience to FastAPI.

## Stack

* **Python 3.x** (tested on 3.12), managed with Poetry
* **FastAPI**
* **Celery** 
* **Redis**
* **Docker**
* **PostgreSQL**
* **S3/MinIO**


## Quick start

```bash
poetry install
# start Redis, Postgres, MinIO
docker-compose up -d
# run db migrations once Postgres is up
alembic upgrade head
# dev server
poetry run uvicorn app.main:app --reload
# start background worker for audio processing
poetry run celery -A app.celery_app worker  --loglevel=info
```

Open **[http://localhost:8000/docs](http://localhost:8000/docs)** for interactive Swagger.

## Tests

```bash
poetry run pytest
```

## Roadmap

* CI/CD: GitHub Actions + Docker‑based integration tests
* Add endpoint that allows tracking of background task status
* Graceful handling of corrupt audio files
* Dockerize API and Celery workers
* Guard against malicious input
