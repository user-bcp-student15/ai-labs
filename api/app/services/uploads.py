import re
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path

from fastapi import UploadFile

ALLOWED_EXTENSIONS = frozenset({".txt", ".md", ".pdf", ".docx"})
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
READ_CHUNK_BYTES = 64 * 1024
SAFE_FILE_NAME = re.compile(r"\w[\w .\-]*")


class UploadRejectedError(Exception):
    def __init__(self, status: HTTPStatus, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


@dataclass(frozen=True)
class StoredUpload:
    file_name: str
    size: int


def sanitize_file_name(raw_name: str | None) -> str:
    name = Path((raw_name or "").replace("\\", "/")).name
    if not SAFE_FILE_NAME.fullmatch(name):
        raise UploadRejectedError(HTTPStatus.BAD_REQUEST, "Invalid file name")
    return name


def validate_extension(file_name: str) -> None:
    if Path(file_name).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise UploadRejectedError(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "File type not allowed")


async def read_limited(upload: UploadFile) -> bytes:
    content = bytearray()
    while chunk := await upload.read(READ_CHUNK_BYTES):
        content.extend(chunk)
        if len(content) > MAX_UPLOAD_BYTES:
            raise UploadRejectedError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "File too large")
    return bytes(content)


async def store_upload(upload_dir: str, upload: UploadFile) -> StoredUpload:
    file_name = sanitize_file_name(upload.filename)
    validate_extension(file_name)
    content = await read_limited(upload)
    (Path(upload_dir) / file_name).write_bytes(content)
    return StoredUpload(file_name=file_name, size=len(content))
