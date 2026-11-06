"""Create the evidence bucket if it does not exist yet. Safe to run on every deploy."""

import logging

from botocore.exceptions import ClientError

from jalada.adapters.storage.s3_store import create_s3_client
from jalada.config.settings import Settings, load_settings

logger = logging.getLogger("jalada.storage")

MISSING = {"404", "NoSuchBucket", "NotFound"}


def main() -> None:
    ensure_bucket(load_settings())


def ensure_bucket(settings: Settings) -> None:
    """Creates the bucket only when it is missing.

    A key limited to one bucket, as recommended for Cloudflare R2, may not be allowed to look
    at the bucket itself. That answer is not "missing", so start-up carries on.
    """
    client = create_s3_client(
        endpoint_url=settings.storage_endpoint_url,
        region=settings.storage_region,
        access_key=settings.storage_access_key,
        secret_key=settings.storage_secret_key.get_secret_value(),
    )
    try:
        client.head_bucket(Bucket=settings.storage_bucket)
    except ClientError as error:
        code = str(error.response.get("Error", {}).get("Code", ""))
        if code not in MISSING:
            logger.warning("could not check the evidence bucket (%s); carrying on", code)
            return
        client.create_bucket(Bucket=settings.storage_bucket)
