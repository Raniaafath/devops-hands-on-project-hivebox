import pytest  # type: ignore
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from main import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def _mock_response(temp_value):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "sensors": [
            {
                "title": "Temperatur",
                "lastMeasurement": {
                    "value": str(temp_value),
                    "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                },
            }
        ]
    }
    return mock_resp

def test_version(client):
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json["version"] == "v0.0.1"

@patch("main.requests.get")
def test_temperature_good(mock_get, client):
    mock_get.return_value = _mock_response(20)
    response = client.get("/temperature")
    assert response.status_code == 200
    assert response.json["average_temperature"] == 20
    assert response.json["status"] == "Good"

@patch("main.requests.get")
def test_temperature_too_cold(mock_get, client):
    mock_get.return_value = _mock_response(5)
    response = client.get("/temperature")
    assert response.status_code == 200
    assert response.json["average_temperature"] == 5
    assert response.json["status"] == "Too Cold"

@patch("main.requests.get")
def test_temperature_too_hot(mock_get, client):
    mock_get.return_value = _mock_response(40)
    response = client.get("/temperature")
    assert response.status_code == 200
    assert response.json["average_temperature"] == 40
    assert response.json["status"] == "Too Hot"

@patch("main.requests.get")
def test_temperature_no_recent_data(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"sensors": []}
    mock_get.return_value = mock_resp

    response = client.get("/temperature")
    assert response.status_code == 404
    assert "error" in response.json
