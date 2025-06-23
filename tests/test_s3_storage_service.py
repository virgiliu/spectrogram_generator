from typing import Iterator
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from botocore.exceptions import ClientError

from app.services.s3_storage import S3StorageService
from tests.utils import MockAsyncContextManager


@pytest.fixture
def bucket_name() -> str:
    return "test-bucket"


@pytest.fixture
def mock_s3_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_async_context_manager(mock_s3_client: AsyncMock) -> MockAsyncContextManager:
    return MockAsyncContextManager(mock_s3_client)


@pytest.fixture
def patch_s3_client(
    mock_async_context_manager: MockAsyncContextManager,
) -> Iterator[None]:
    """Patches aioboto3 so that every 'session.client(...)' call inside the service
    yields our mocked S3 client via an async context-manager.
    """
    with patch(
        "app.services.s3_storage.aioboto3.Session.client",
        return_value=mock_async_context_manager,
    ):
        yield


@pytest.mark.asyncio
async def test_for_bucket_returns_instance(
    patch_s3_client: None, mock_s3_client: AsyncMock, bucket_name: str
):
    async with S3StorageService.for_bucket(bucket_name) as service:
        mock_s3_client.head_bucket.assert_awaited_once_with(Bucket=bucket_name)

    assert isinstance(service, S3StorageService)
    assert service._bucket_name == bucket_name


@pytest.mark.asyncio
async def test_init_raises_if_bucket_missing(
    patch_s3_client: None, mock_s3_client: AsyncMock, bucket_name: str
):
    mock_s3_client.head_bucket.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadBucket"
    )

    with pytest.raises(ClientError) as exc:
        async with S3StorageService.for_bucket(bucket_name):
            pass  # Error should occur when entering context

    assert exc.value.response["Error"]["Code"] == "404"


@pytest.mark.asyncio
async def test_store_success(
    patch_s3_client: None, mock_s3_client: AsyncMock, bucket_name: str
):
    uuid = uuid4()
    data = b"Bist du ohne Herz geboren oder hast du es verloren?"

    async with S3StorageService.for_bucket(bucket_name) as service:
        await service.store(uuid, data)

    mock_s3_client.put_object.assert_awaited_once_with(
        Bucket=bucket_name, Key=str(uuid), Body=data, ContentType=""
    )


@pytest.mark.asyncio
async def test_retrieve_success(
    patch_s3_client: None, mock_s3_client: AsyncMock, bucket_name: str
):
    uuid = uuid4()

    expected_data = b"Du hast mich gefragt und ich hab' nichts gesagt"

    mock_body = AsyncMock()
    mock_body.read.return_value = expected_data
    mock_body.__aenter__.return_value = mock_body

    mock_s3_client.get_object.return_value = {"Body": mock_body}

    async with S3StorageService.for_bucket(bucket_name) as service:
        result = await service.retrieve(uuid)

    assert result == expected_data

    mock_s3_client.get_object.assert_awaited_once_with(
        Bucket=bucket_name, Key=str(uuid)
    )


@pytest.mark.asyncio
async def test_retrieve_inexistent_uuid_raises_404(
    patch_s3_client: None, mock_s3_client: AsyncMock, bucket_name: str
):
    uuid = uuid4()

    mock_s3_client.get_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "Not Found"}}, "GetObject"
    )

    async with S3StorageService.for_bucket(bucket_name) as service:
        with pytest.raises(ClientError) as exc:
            await service.retrieve(uuid)

    assert exc.value.response["Error"]["Code"] == "NoSuchKey"
    mock_s3_client.get_object.assert_awaited_once_with(
        Bucket=bucket_name, Key=str(uuid)
    )
