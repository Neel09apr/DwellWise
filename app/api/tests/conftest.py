import pytest
from fastapi.testclient import TestClient

from dwellwise_api.config import Settings
from dwellwise_api.main import create_app


@pytest.fixture
def client() -> TestClient:
    with TestClient(create_app(Settings())) as c:
        yield c
