import logging
from dataclasses import dataclass

import urllib3

from app.config import HEALTH_TIMEOUT_SECONDS

UNREACHABLE_STATUS = 0
UNAVAILABLE_MESSAGE = "Backend unavailable"

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BackendHealth:
    status: int
    body: str


def check_backend_health(url: str) -> BackendHealth:
    try:
        response = urllib3.PoolManager().request("GET", url, timeout=HEALTH_TIMEOUT_SECONDS)
        return BackendHealth(status=response.status, body=response.data.decode("utf-8"))
    except (urllib3.exceptions.HTTPError, UnicodeDecodeError) as error:
        logger.warning("Backend health check failed: %s", error)
        return BackendHealth(status=UNREACHABLE_STATUS, body=UNAVAILABLE_MESSAGE)
