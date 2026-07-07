import requests
import json

def dispatch_critical_alert(webhook_url: str, employee_id: str, risk_score, mitigation_note: str):
    """
    Dispatches a Block Kit payload to a Slack webhook. Uses simulated execution if missing valid URL configurations.
    """
    risk_display = f"{risk_score:.1f}%" if isinstance(risk_score, (float, int)) else str(risk_score)

    if not webhook_url or not webhook_url.startswith("https://hooks.slack.com"):
        print(f"[SIMULATION] Slack Alert for {employee_id} (Risk: {risk_display}) triggered.")
        return True

    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 CRITICAL FLIGHT RISK ALERT 🚨",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Employee ID:*\n{employee_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Risk Score:*\n{risk_display}"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*AI Recommended Mitigation:*\n```\n{mitigation_note}\n```"
                }
            }
        ]
    }
    
    try:
        response = requests.post(
            webhook_url, data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to trigger Slack Webhook: {e}")
        return False
