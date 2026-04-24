from __future__ import annotations

import os
from importlib import import_module

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "diagnostix.settings")

celery_module = import_module("celery")
app = celery_module.Celery("diagnostix")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


