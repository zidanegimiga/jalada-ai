from typing import TYPE_CHECKING
from uuid import UUID

from jalada.modules.evidence.adapters.cipher import EvidenceCipher

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


class EncryptedS3EvidenceStore:
    """Evidence in any S3-compatible bucket (MinIO, R2, S3). The bucket only sees ciphertext."""

    def __init__(self, client: "S3Client", bucket: str, ciphers: list[EvidenceCipher]) -> None:
        self._client = client
        self._bucket = bucket
        # The first cipher encrypts new objects. The others still decrypt older ones.
        self._ciphers = {cipher.key_id: cipher for cipher in ciphers}
        self.key_id = ciphers[0].key_id

    def put(self, evidence_id: UUID, user_id: UUID, data: bytes) -> None:
        name = _object_name(evidence_id, user_id)
        sealed = self._ciphers[self.key_id].encrypt(data, name.encode())
        self._client.put_object(Bucket=self._bucket, Key=name, Body=sealed)

    def get(self, evidence_id: UUID, user_id: UUID, key_id: str) -> bytes:
        name = _object_name(evidence_id, user_id)
        sealed = self._client.get_object(Bucket=self._bucket, Key=name)["Body"].read()
        return self._ciphers[key_id].decrypt(sealed, name.encode())

    def delete(self, evidence_id: UUID, user_id: UUID) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=_object_name(evidence_id, user_id))


def _object_name(evidence_id: UUID, user_id: UUID) -> str:
    return f"evidence/{user_id}/{evidence_id}"
