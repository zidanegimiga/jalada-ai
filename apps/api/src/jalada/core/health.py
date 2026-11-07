"""Checks that the API can reach what it depends on, for /health/ready."""

import logging
from typing import TYPE_CHECKING

from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

logger = logging.getLogger("jalada.health")

# Never stored. Asking for it proves the bucket exists and the key may read from it.
PROBE_KEY = "health-check/never-stored"
# For the storage check's own client: answer quickly, so an uptime monitor gets a 503
# rather than a timeout when storage hangs.
QUICK = Config(connect_timeout=2, read_timeout=3, retries={"total_max_attempts": 1})


class DatabaseCheck:
    name = "database"

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ok(self) -> bool:
        try:
            with self._engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError as error:
            logger.warning("database check failed with %s", type(error).__name__)
            return False
        return True


class StorageCheck:
    name = "storage"

    def __init__(self, client: "S3Client", bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    def ok(self) -> bool:
        """A missing object is the healthy answer. A missing bucket or a refused key is not."""
        try:
            self._client.get_object(Bucket=self._bucket, Key=PROBE_KEY)
        except ClientError as error:
            code = error.response.get("Error", {}).get("Code", "")
            if code in ("NoSuchKey", "404"):
                return True
            logger.warning("storage check failed with %s", code)
            return False
        except BotoCoreError as error:
            logger.warning("storage check failed with %s", type(error).__name__)
            return False
        return True
