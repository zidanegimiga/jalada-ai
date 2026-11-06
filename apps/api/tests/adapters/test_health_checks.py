from typing import Any

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from jalada.adapters.health import StorageCheck


class Bucket:
    """Stands in for the S3 client: raises what a real store would for the probe key."""

    def __init__(self, error: Exception | None) -> None:
        self._error = error

    def get_object(self, **_: Any) -> dict[str, Any]:
        if self._error:
            raise self._error
        return {}


def client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code}}, "GetObject")


@pytest.mark.parametrize(
    ("error", "healthy"),
    [
        (client_error("NoSuchKey"), True),
        (client_error("404"), True),
        (None, True),
        (client_error("NoSuchBucket"), False),
        (client_error("AccessDenied"), False),
        (client_error("InvalidAccessKeyId"), False),
        (EndpointConnectionError(endpoint_url="https://storage.example.com"), False),
    ],
    ids=["missing-key", "missing-key-head", "found", "no-bucket", "denied", "bad-key", "down"],
)
def test_storage_is_healthy_only_when_the_bucket_answers(
    error: Exception | None, healthy: bool
) -> None:
    assert StorageCheck(Bucket(error), "bucket").ok() is healthy  # type: ignore[arg-type]
