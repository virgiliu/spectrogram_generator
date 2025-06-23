class MockAsyncContextManager:
    """Mock for async context managers yielding a given mock.

    Example:
        from unittest.mock import AsyncMock, patch

        # Create a mock object
        mock_resource = AsyncMock()

        # Simulate an error on a method call
        mock_resource.some_method.side_effect = Exception("Boom!")

        # Wrap in mocked async context manager
        mock_cm = MockAsyncContextManager(mock_resource)

        # Patch an async context manager to yield our mock
        with patch("some.module.AsyncSession", return_value=mock_cm):
            # Now, 'async with AsyncSession() as resource:' yields mock_resource
            # and 'await resource.some_method()' will raise Exception("Boom!")
            ...
    """

    def __init__(self, mock):
        self.mock = mock

    async def __aenter__(self):
        return self.mock

    async def __aexit__(self, exc_type, exc, tb):
        return False  # Don't suppress exceptions

    # Optional: allow attribute passthrough or chaining
    def __getattr__(self, item):
        return getattr(self.mock, item)
