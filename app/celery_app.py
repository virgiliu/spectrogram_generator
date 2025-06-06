from celery import Celery

celery_app = Celery(
    "tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0"
)

celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.task_acks_on_failure_or_timeout = False

celery_app.autodiscover_tasks(["app.tasks"], related_name="audio")
