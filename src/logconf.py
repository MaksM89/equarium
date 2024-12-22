import contextvars
import logging.config
import uuid
from typing import Callable, Coroutine, Any

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_extra = contextvars.ContextVar('extra')

LOGLEVEL = logging.INFO

class LoggerMiddleware(BaseHTTPMiddleware):
    """Добавляет экстра инфу для логирования"""

    async def dispatch(
            self,
            request: Request,
            call_next: Callable[[Request], Coroutine[Any, Any, Response]],
    ) -> Response:
        request_id: str = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        try:
            user_id = jwt.decode(
                request.headers.get('Authorization', 'Bearer ..')[len('Bearer '):],
                options={"verify_signature": False}).get('sub', 'unknown')
        except jwt.PyJWTError:
            user_id = 'unknown'
        _extra.set(dict(request_id=request_id, user_id=user_id))
        response = await call_next(request)
        return response

class InjectingFilter(logging.Filter):
    """
    A filter which injects context-specific information into logs
    """
    def filter(self, record):
        for k, v in _extra.get(dict(user_id='', request_id='')).items():
            setattr(record, k, v)
        return True

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters':{
        'InjectingFilter': {
            '()': InjectingFilter,
        }
    },
    'formatters': {
        'standard': {
            'format': '[%(levelname)s] %(name)s u_%(user_id)s r_%(request_id)s: %(message)s',
            'datefmt': "%Y.%m.%d %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
            'level': LOGLEVEL,
            'filters': ['InjectingFilter'],
        },
    },
    'loggers': {
        'uvicorn': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'sqlalchemy': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'passlib': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'auth': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'trans': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)