import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def isolate_cache():
    """Keep rate limits and other cached state independent between tests."""
    cache.clear()
    yield
    cache.clear()
