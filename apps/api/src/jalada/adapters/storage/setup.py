"""Create the evidence bucket if it does not exist yet. Safe to run on every deploy."""

from botocore.exceptions import ClientError

from jalada.adapters.storage.s3_store import create_s3_client
from jalada.config.settings import load_settings


def main() -> None:
    settings = load_settings()
    client = create_s3_client(
        endpoint_url=settings.storage_endpoint_url,
        region=settings.storage_region,
        access_key=settings.storage_access_key,
        secret_key=settings.storage_secret_key.get_secret_value(),
    )
    try:
        client.head_bucket(Bucket=settings.storage_bucket)
    except ClientError:
        client.create_bucket(Bucket=settings.storage_bucket)
