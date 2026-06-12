import pytest  # type: ignore
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def mock_box_response(value, age_seconds=0):
    measured_at = datetime.now(timezone.utc) - timedelta(seconds=age_seconds)
    response = MagicMock()
    response.json.return_value = {
        "sensors": [
            {
                "title": "Temperature",
                "lastMeasurement": {
                    "value": str(value),
                    "createdAt": measured_at.isoformat(),
                },
            }
        ]
    }
    return response


def test_version(client):
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json["version"] == "v0.0.1"


def test_metrics(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.content_type.startswith("text/plain")
    assert b"python_info" in response.data


@patch("main.requests.get")
def test_temperature_too_cold(mock_get, client):
    mock_get.return_value = mock_box_response(5)
    response = client.get("/temperature")
    assert response.status_code == 200
    assert response.json["average_temperature"] == 5
    assert response.json["status"] == "Too Cold"


@patch("main.requests.get")
def test_temperature_good(mock_get, client):
    mock_get.return_value = mock_box_response(20)
    response = client.get("/temperature")
    assert response.status_code == 200
    assert response.json["average_temperature"] == 20
    assert response.json["status"] == "Good"


@patch("main.requests.get")
def test_temperature_too_hot(mock_get, client):
    mock_get.return_value = mock_box_response(40)
    response = client.get("/temperature")
    assert response.status_code == 200
    assert response.json["average_temperature"] == 40
    assert response.json["status"] == "Too Hot"


@patch("main.requests.get")
def test_temperature_no_recent_data(mock_get, client):
    mock_get.return_value = mock_box_response(20, age_seconds=7200)
    response = client.get("/temperature")
    assert response.status_code == 404
    assert "error" in response.json
