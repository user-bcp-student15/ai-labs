import base64
import logging
import time

from fastapi import Header, HTTPException

from app.schemas import Identity

LEGACY_SECRET = "WORKSHOP_SECRET_2026"
BEARER_PREFIX = "Bearer "
TOKEN_PART_COUNT = 4
INVALID_TOKEN_MESSAGE = "Invalid token"

logger = logging.getLogger(__name__)


def legacy_identity(authorization: str = Header(default="")) -> Identity:
    try:
        token = authorization.replace(BEARER_PREFIX, "")
        decoded = base64.b64decode(token).decode("utf-8")
        parts = decoded.split("|")
        if len(parts) != TOKEN_PART_COUNT or parts[3] != LEGACY_SECRET or int(parts[2]) < int(time.time()):
            raise ValueError("invalid token")
        return Identity(username=parts[0], role=parts[1])
    except ValueError as error:
        logger.warning("Token rejected: %s", error)
        raise HTTPException(status_code=401, detail=INVALID_TOKEN_MESSAGE) from error
