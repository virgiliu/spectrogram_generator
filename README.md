## ⚠️ Security notice

This repository intentionally includes `.env` and credentials in docker-compose.


They are dummy, local-only values used for demonstration purposes.

No real keys, tokens, or production systems are involved, this project is purely for fun and learning.



# Spectrogram Generator - Async Media Processing API

FastAPI-based asynchronous microservice that converts uploaded audio files into spectrogram images using Celery workers and Redis queues.
Designed as a minimal example of a scalable distributed task system with clean separation between API, background workers, and storage.


## Stack

| Component                   | Purpose                                        |
| --------------------------- | ---------------------------------------------- |
| **FastAPI**                 | Handles upload requests and task orchestration |
| **Celery + Redis**          | Asynchronous job queue for audio processing    |
| **PostgreSQL + SQLAlchemy** | Tracks task metadata and results               |
| **S3 / MinIO**              | Stores raw audio and generated spectrograms    |
| **Docker Compose**          | Local orchestration of all services            |


## Why

Originally built to refresh my FastAPI experience and demonstrate horizontal scaling for CPU-bound media workloads, similar design used for image or video processing pipelines.

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
* Task-status endpoint + progress tracking
* Graceful handling of corrupt or malicious uploads
* Dockerize API and Celery workers
