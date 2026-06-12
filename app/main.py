import os
from flask import Flask, jsonify
import requests
from datetime import datetime, timezone
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

APP_VERSION = "v0.0.1"

app = Flask(__name__)

DEFAULT_SENSEBOX_IDS = "5eba5fbad46fb8001b799786,5c21ff8f919bf8001adf2488,5ade1acf223bd80019a1011c"
SENSEBOX_IDS = os.environ.get("SENSEBOX_IDS", DEFAULT_SENSEBOX_IDS).split(",")

@app.route("/version")
def version():
    """Return the current application version as JSON."""
    return jsonify({"version": APP_VERSION})

@app.route("/metrics")
def metrics():
    """Expose default Prometheus metrics."""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

def temperature_status(avg_temp):
    """Classify an average temperature into a status label."""
    if avg_temp < 10:
        return "Too Cold"
    if avg_temp > 36:
        return "Too Hot"
    return "Good"

@app.route("/temperature")
def temperature():
    """Fetch recent temperature readings and return the average."""
    temperatures = []

    for box_id in SENSEBOX_IDS:
        url = f"https://api.opensensemap.org/boxes/{box_id}?format=json"
        response = requests.get(url, timeout=5)
        box = response.json()

        for sensor in box.get("sensors", []):
            if "temp" in sensor.get("title", "").lower():
                last_measurement = sensor.get("lastMeasurement")
                if last_measurement:
                    measured_at = datetime.fromisoformat(
                        last_measurement["createdAt"].replace("Z", "+00:00")
                    )
                    age = datetime.now(timezone.utc) - measured_at
                    if age.total_seconds() <= 3600:
                        temperatures.append(float(last_measurement["value"]))

    if not temperatures:
        return jsonify({"error": "No recent temperature data"}), 404

    avg_temp = round(sum(temperatures) / len(temperatures), 2)
    return jsonify({"average_temperature": avg_temp, "status": temperature_status(avg_temp)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)