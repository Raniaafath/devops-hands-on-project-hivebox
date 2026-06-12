import pytest  # type: ignore
from main import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_version(client):
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json["version"] == "v0.0.1"

def test_temperature(client):
    response = client.get("/temperature")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert "average_temperature" in response.json