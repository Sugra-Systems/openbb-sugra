"""Shared test fixtures for openbb-sugra."""

import os

import pytest


@pytest.fixture(scope="session")
def api_key() -> str | None:
    """Return the Sugra API key from the environment, if set."""
    return os.environ.get("SUGRA_TEST_API_KEY")


@pytest.fixture()
def credentials(api_key: str | None) -> dict[str, str]:
    """Credentials for live tests; skips when no key is configured."""
    if not api_key:
        pytest.skip("SUGRA_TEST_API_KEY not set - skipping live data test.")
    return {"sugra_api_key": api_key}
