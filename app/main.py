import os

from flask import Flask, jsonify
import requests
from datetime import datetime, timezone
from prometheus_flask_exporter import PrometheusMetrics

APP_VERSION = "v0.0.1"

app = Flask(__name__)
metrics = PrometheusMetrics(app)

SENSEBOX_IDS = os.environ.get(
    "SENSEBOX_IDS",
    "5eba5fbad46fb8001b799786,5c21ff8f919bf8001adf2488,5ade1acf223bd80019a1011c"
).split(",")

@app.route("/version")
def version():
    """Return the current application version as JSON."""
    return jsonify({"version": APP_VERSION})

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

    avg_temp = sum(temperatures) / len(temperatures)
    avg = round(avg_temp, 2)

    if avg < 10:
        status = "Too Cold"
    elif avg <= 36:
        status = "Good"
    else:
        status = "Too Hot"

    return jsonify({"average_temperature": avg, "status": status})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)