import base64
import logging
import time

from fastapi import Header, HTTPException

from app.schemas import Identity

LEGACY_SECRET = "WORKSHOP_SECRET_2026"
BEARER_PREFIX = "Bearer "
TOKEN_PART_COUNT = 4
INVALID_TOKEN_MESSAGE = "Invalid token"
MAX_TOKEN_TTL_SECONDS = 5
ACCEPTED_ROLES = frozenset({"TRAINER"})

logger = logging.getLogger(__name__)


def legacy_identity(authorization: str = Header(default="")) -> Identity:
    try:
        token = authorization.replace(BEARER_PREFIX, "")
        decoded = base64.b64decode(token).decode("utf-8")
        parts = decoded.split("|")
        if len(parts) != TOKEN_PART_COUNT or parts[3] != LEGACY_SECRET:
            raise ValueError("invalid token")
        if not parts[0].strip() or parts[1] not in ACCEPTED_ROLES:
            raise ValueError("invalid token")
        expires_at = int(parts[2])
        now = int(time.time())
        if expires_at <= now or expires_at - now > MAX_TOKEN_TTL_SECONDS:
            raise ValueError("invalid token")
        return Identity(username=parts[0], role=parts[1])
    except ValueError as error:
        logger.warning("Token rejected: %s", error)
        raise HTTPException(status_code=401, detail=INVALID_TOKEN_MESSAGE) from error
