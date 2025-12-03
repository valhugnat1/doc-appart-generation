import os
import pytest
os.environ["ANTHROPIC_API_KEY"] = "dummy"
os.environ["OPENAI_API_KEY"] = "dummy"

from fastapi.testclient import TestClient
from fastapi_app.main import app

@pytest.fixture
def client():
    return TestClient(app)
