import pytest  # type: ignore
from main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.mark.integration
def test_version_live(client):
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json["version"] == "v0.0.1"


@pytest.mark.integration
def test_temperature_live(client):
    response = client.get("/temperature")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        assert "average_temperature" in response.json
        assert response.json["status"] in ("Too Cold", "Good", "Too Hot")


@pytest.mark.integration
def test_metrics_live(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.content_type.startswith("text/plain")
