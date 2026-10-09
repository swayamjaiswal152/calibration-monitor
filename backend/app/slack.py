import os
import requests

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "")

def send_slack_alert(sensor_id: str, picp: float, target: float = 0.9):
    if not SLACK_WEBHOOK:
        print(f"[ALERT-SKIPPED] No SLACK_WEBHOOK set. Drift on {sensor_id}: PICP {picp:.2%}")
        return False
    payload = {
        "text": f"🚨 *Forecast Drift Detected*",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": "🚨 Forecast Calibration Drift"}},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*Sensor:*\n`{sensor_id}`"},
                {"type": "mrkdwn", "text": f"*Coverage:*\n`{picp:.2%}` < Target `{target:.0%}`"},
                {"type": "mrkdwn", "text": f"*Status:*\n:warning: Interval Miscalibrated"},
                {"type": "mrkdwn", "text": f"*Action:*\nRun Conformal Auto-Correct"}
            ]},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": "Sent by calibration-monitor | <http://localhost:5173|View Dashboard>"}]}
        ]
    }
    try:
        r = requests.post(SLACK_WEBHOOK, json=payload, timeout=5)
        print(f"[SLACK] Sent: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print(f"[SLACK ERROR] {e}")
        return False

# For testing without Slack use https://webhook.site
def send_webhook_test(url: str):
    return requests.post(url, json={"test": "calibration-monitor webhook works!"})