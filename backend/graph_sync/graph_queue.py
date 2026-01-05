import threading
from queue import Queue, Empty

from django.utils import timezone


_QUEUE = Queue()
_WORKER = None
_LOCK = threading.Lock()


def start_worker():
    global _WORKER
    with _LOCK:
        if _WORKER and _WORKER.is_alive():
            return
        _WORKER = threading.Thread(target=_run, name="graph-sync-worker", daemon=True)
        _WORKER.start()


def enqueue(task_name: str, payload: dict):
    _QUEUE.put({"task": task_name, "payload": payload})


def enqueue_report_sync(report_id: int):
    enqueue("sync_report", {"report_id": report_id})


def enqueue_recommendations(report_id: int, user_id: str, language: str):
    enqueue(
        "recommendations",
        {"report_id": report_id, "user_id": user_id, "language": language},
    )


def _run():
    while True:
        try:
            item = _QUEUE.get(timeout=0.5)
        except Empty:
            continue
        task = item.get("task")
        payload = item.get("payload") or {}
        try:
            if task == "sync_report":
                _task_sync_report(payload)
            elif task == "recommendations":
                _task_recommendations(payload)
            elif task == "user_similarity":
                _task_user_similarity(payload)
        except Exception as exc:
            print(f"[graph_sync] task failed ({task}): {exc}", flush=True)
        finally:
            _QUEUE.task_done()


def _task_sync_report(payload: dict):
    from api.models import LivecodingReport
    from graph_sync.service import ensure_graph_sources, sync_report_to_graph

    report_id = payload.get("report_id")
    report = LivecodingReport.objects.filter(id=report_id).select_related("user").first()
    if not report:
        return
    ensure_graph_sources()
    sync_report_to_graph(report, report.user, report.graph_output or {})
    enqueue("user_similarity", {"user_id": str(report.user.user_id)})


def _task_recommendations(payload: dict):
    from api.models import LivecodingReport
    from graph_sync.recommendations import build_recommended_problems
    from graph_sync.service import ensure_graph_sources

    report_id = payload.get("report_id")
    user_id = payload.get("user_id")
    language = (payload.get("language") or "python").lower()

    report = LivecodingReport.objects.filter(id=report_id).first()
    if not report:
        return

    graph_output = report.graph_output or {}
    if graph_output.get("recommended_problems"):
        return

    ensure_graph_sources()
    recs = build_recommended_problems(
        user_id=str(user_id),
        graph_output=graph_output,
        limit=3,
        language=language,
    )
    if not recs:
        return

    graph_output["recommended_problems"] = recs
    report.graph_output = graph_output
    report.updated_at = timezone.localtime(timezone.now())
    report.save(update_fields=["graph_output", "updated_at"])


def _task_user_similarity(payload: dict):
    from graph_sync.user_similarity import update_user_similarity

    user_id = payload.get("user_id")
    if not user_id:
        return
    update_user_similarity(str(user_id))
