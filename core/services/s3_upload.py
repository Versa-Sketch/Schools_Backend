import os
import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings

from core import constants
from core.exceptions import ValidationException


# ---------------------------------------------------------------------------
# Allowed MIME type sets — import these when calling upload_to_s3
# ---------------------------------------------------------------------------

IMAGE_TYPES = {
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/gif',
}

VIDEO_TYPES = {
    'video/mp4',
    'video/quicktime',
    'video/x-msvideo',
    'video/x-matroska',
}

DOCUMENT_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
}

PROFILE_PIC_TYPES = IMAGE_TYPES
ATTACHMENT_TYPES = IMAGE_TYPES | VIDEO_TYPES | DOCUMENT_TYPES

# 50 MB default max size
DEFAULT_MAX_SIZE_BYTES = 50 * 1024 * 1024


# ---------------------------------------------------------------------------
# Core upload function
# ---------------------------------------------------------------------------

def upload_to_s3(
    file_obj,
    folder: str,
    allowed_types: set = None,
    max_size_bytes: int = DEFAULT_MAX_SIZE_BYTES,
) -> str:
   
    content_type = getattr(file_obj, 'content_type', None) or 'application/octet-stream'
    if allowed_types and content_type not in allowed_types:
        raise ValidationException(
            f"File type '{content_type}' is not allowed. "
            f"Allowed types: {', '.join(sorted(allowed_types))}."
        )

    # --- Validate file size ---
    file_size = getattr(file_obj, 'size', None)
    if file_size is None:
        file_obj.seek(0, 2)
        file_size = file_obj.tell()
        file_obj.seek(0)
    if file_size > max_size_bytes:
        raise ValidationException(
            f"File size {file_size} bytes exceeds the maximum allowed "
            f"{max_size_bytes} bytes ({max_size_bytes // (1024 * 1024)} MB)."
        )

    # --- Build S3 key ---
    original_name = getattr(file_obj, 'name', '') or ''
    ext = os.path.splitext(original_name)[1].lower()
    key = f"{folder}/{uuid.uuid4()}{ext}"

    # --- Upload ---
    try:
        client = boto3.client(
            's3',
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        file_obj.seek(0)
        client.upload_fileobj(
            file_obj,
            settings.AWS_STORAGE_BUCKET_NAME,
            key,
            ExtraArgs={
                'ContentType': content_type,
                'ACL': 'public-read',
            },
        )
    except (BotoCoreError, ClientError) as exc:
        raise ValidationException(
            f"File upload failed: {exc}",
            code=constants.UPLOAD_FAILED,
        )

    url = (
        f"https://{settings.AWS_STORAGE_BUCKET_NAME}"
        f".s3.{settings.AWS_S3_REGION_NAME}"
        f".amazonaws.com/{key}"
    )
    return url
