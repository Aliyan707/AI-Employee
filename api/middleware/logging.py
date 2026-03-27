"""
api/middleware/logging.py — Structured JSON request logging middleware.

Logs every request with method, path, status code, duration, and request ID.
Masks PII (email, phone) in log output.
"""

import json
import logging
import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("api.requests")

# Regex patterns for PII masking
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"\+?[1-9]\d{7,14}")


def mask_pii(text: str) -> str:
    """Mask email addresses and phone numbers in log strings."""
    text = EMAIL_PATTERN.sub("***@***.***", text)
    text = PHONE_PATTERN.sub("***", text)
    return text


class JSONLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs each HTTP request as a structured JSON object.

    Log format:
    {
        "timestamp": "ISO8601",
        "request_id": "uuid",
        "method": "POST",
        "path": "/webhooks/webform",
        "status_code": 200,
        "duration_ms": 342,
        "client_ip": "127.0.0.1"
    }
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.monotonic()

        # Attach request ID to request state for downstream use
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            logger.exception("Unhandled exception in request %s", request_id)
            raise exc
        finally:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            path = mask_pii(str(request.url.path))

            log_entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else "unknown",
            }
            logger.info(json.dumps(log_entry))

        return response
