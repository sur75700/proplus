import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.observability.logger import JSONLogger

logger = JSONLogger()

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()

        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response: Response = await call_next(request)

        latency = (time.time() - start) * 1000

        response.headers["X-Request-ID"] = request_id

        logger.log({
            "type": "request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "latency_ms": round(latency, 2)
        })

        return response
