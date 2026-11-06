from typing import Any

import pytest
from botocore.exceptions import ClientError
from conftest import make_settings

from jalada.adapters.storage import setup


class Bucket:
    def __init__(self, head_error: str | None) -> None:
        self.head_error = head_error
        self.created: list[str] = []

    def head_bucket(self, Bucket: str) -> None:  # noqa: N803 (boto3's own argument name)
        if self.head_error:
            raise ClientError({"Error": {"Code": self.head_error}}, "HeadBucket")

    def create_bucket(self, Bucket: str) -> None:  # noqa: N803
        self.created.append(Bucket)


@pytest.mark.parametrize(
    ("head_error", "created"),
    [(None, []), ("404", ["jalada-evidence"]), ("NoSuchBucket", ["jalada-evidence"]), ("403", [])],
)
def test_the_bucket_is_only_created_when_missing(
    monkeypatch: pytest.MonkeyPatch, head_error: str | None, created: list[str]
) -> None:
    bucket = Bucket(head_error)
    monkeypatch.setattr(setup, "create_s3_client", lambda **_: bucket)

    setup.ensure_bucket(make_settings())

    assert bucket.created == created


def test_other_failures_are_not_swallowed(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(**_: Any) -> None:
        raise ConnectionError("storage unreachable")

    monkeypatch.setattr(setup, "create_s3_client", broken)

    with pytest.raises(ConnectionError):
        setup.ensure_bucket(make_settings())
