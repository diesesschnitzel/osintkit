import pytest


@pytest.fixture
def sample_target():
    return {
        "name": "Test User",
        "email": "test@example.com",
        "username": "testuser",
        "phone": "+15555550100",
    }


@pytest.fixture
def empty_config():
    return {
        "api_keys": {},
        "timeout_seconds": 10,
        "output_dir": "~/osint-results",
    }
