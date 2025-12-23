import contextvars
import logging

user_id_var = contextvars.ContextVar("user_id", default="-")
session_id_var = contextvars.ContextVar("session_id", default="-")
request_id_var = contextvars.ContextVar("request_id", default="-")


def set_context(*, user_id: str | None = None, session_id: str | None = None, request_id: str | None = None) -> None:
    if user_id is not None:
        user_id_var.set(str(user_id))
    if session_id is not None:
        session_id_var.set(str(session_id))
    if request_id is not None:
        request_id_var.set(str(request_id))


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.user_id = user_id_var.get()
        record.session_id = session_id_var.get()
        record.request_id = request_id_var.get()

        for attr in ("method", "path", "status_code", "duration_ms"):
            if not hasattr(record, attr):
                setattr(record, attr, "-")

        return True
