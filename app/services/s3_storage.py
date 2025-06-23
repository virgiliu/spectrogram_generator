from __future__ import annotations

import logging
from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncGenerator, Dict
from uuid import UUID

import aioboto3
from aiobotocore.client import AioBaseClient

from app.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def open_s3_stores(
    *buckets: str,
) -> AsyncGenerator[Dict[str, S3StorageService], None]:
    """Async CM that yields a dict {bucket_name: S3StorageService}
    and keeps all underlying clients open until exit.

    Example usage:
    async with open_s3_stores(AUDIO_BUCKET, SPECTROGRAM_BUCKET) as stores:
        audio_store = stores[AUDIO_BUCKET]
        spectrogram_store = stores[SPECTROGRAM_BUCKET]
        ...
    """
    async with AsyncExitStack() as stack:
        stores: Dict[str, S3StorageService] = {}
        for bucket in buckets:
            store = await stack.enter_async_context(S3StorageService.for_bucket(bucket))
            stores[bucket] = store
        # `yield` keeps resources open, `return` would close them
        yield stores


class S3StorageService:
    def __init__(self, bucket_name: str, client: AioBaseClient):
        self._bucket_name = bucket_name
        self._client = client

    async def store(
        self, object_uuid: UUID, data: bytes, content_type: str = ""
    ) -> None:
        await self._client.put_object(
            Bucket=self._bucket_name,
            Key=str(object_uuid),
            Body=data,
            ContentType=content_type,
        )

    async def retrieve(self, object_uuid: UUID) -> bytes:
        resp = await self._client.get_object(
            Bucket=self._bucket_name, Key=str(object_uuid)
        )
        async with resp["Body"] as body:
            return await body.read()

    @classmethod
    @asynccontextmanager
    async def for_bucket(
        cls, bucket_name: str
    ) -> AsyncGenerator[S3StorageService, None]:
        """Example usage:
        from uuid import uuid4
        async with S3StorageService.for_bucket("BucketName") as store:
            uuid = uuid4()
            await store.retrieve(uuid)
        """
        settings = get_settings()
        client_conf = dict(
            service_name="s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ID,
            aws_secret_access_key=settings.S3_SECRET,
        )

        session = aioboto3.Session()

        async with session.client(**client_conf) as client:
            # Check if bucket exists and there's access to it
            await client.head_bucket(Bucket=bucket_name)

            yield cls(bucket_name, client)
