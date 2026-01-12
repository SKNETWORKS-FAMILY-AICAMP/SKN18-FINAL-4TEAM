from django.apps import AppConfig


class GraphSyncConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "graph_sync"

    def ready(self):
        try:
            from .graph_queue import start_worker

            start_worker()
        except Exception as exc:
            print(f"[graph_sync] worker start failed: {exc}", flush=True)
