from locust import HttpUser, task, between
import random

class LoadTest(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_metrics(self): self.client.get("/api/v1/metrics?sensor_id=sensor-1&window=168")
    @task
    def post_forecast(self):
        self.client.post("/api/v1/forecasts", json={
            "sensor_id": "sensor-1", "y_pred": random.uniform(20,30),
            "y_lower": 18, "y_upper": 32
        })