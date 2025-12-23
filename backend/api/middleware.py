import logging
import time
import uuid

import jwt
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from .logging_context import set_context


class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex
        session_id = request.headers.get("X-Session-Id") or request.GET.get("session_id") or "-"
        user_id = "-"

        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user_id = payload.get("sub") or "-"
            except Exception:
                user_id = "-"

        set_context(user_id=user_id, session_id=session_id, request_id=request_id)
        request._log_start = time.monotonic()

    def process_response(self, request, response):
        duration_ms = "-"
        if hasattr(request, "_log_start"):
            duration_ms = int((time.monotonic() - request._log_start) * 1000)

        logger = logging.getLogger("app.request")
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": getattr(response, "status_code", "-"),
                "duration_ms": duration_ms,
            },
        )
        return response

    def process_exception(self, request, exception):
        logger = logging.getLogger("app.request")
        logger.exception("request_error", extra={"path": request.path})
        return None
