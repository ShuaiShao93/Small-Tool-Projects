import os
from typing import List

import requests

from python.models import NormalizedAlertRule

GRAFANA_URL = "https://org.grafana.net"
RULE_GROUP = "API Latency"

API_KEY = os.environ.get("GRAFANA_CLOUD_API_KEY")
assert API_KEY, "GRAFANA_CLOUD_API_KEY environment variable is not set"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def fetch_grafana_alert_rules() -> List[dict]:
    response = requests.get(
        f"{GRAFANA_URL}/api/v1/provisioning/alert-rules", headers=HEADERS
    )
    response.raise_for_status()  # Raises HTTPError for bad responses
    return [alert for alert in response.json() if alert.get("ruleGroup") == RULE_GROUP]


def get_title_to_uid_map(grafana_rules: list[dict]) -> dict:
    title_to_id = {}
    for rule in grafana_rules:
        title = rule.get("title")
        title_to_id[title] = rule.get("uid")
    return title_to_id


def normalize_alert_rules(rules: list[dict]) -> List[NormalizedAlertRule]:
    normalized_rules = [NormalizedAlertRule.from_grafana_rule(rule) for rule in rules]
    return sorted(normalized_rules, key=lambda x: x.title)


def create_alert_rule(alert_rule: NormalizedAlertRule) -> None:
    payload = alert_rule.to_payload()
    response = requests.post(
        f"{GRAFANA_URL}/api/v1/provisioning/alert-rules", json=payload, headers=HEADERS
    )
    if response.status_code == 201:
        print(f"Alert rule '{alert_rule.title}' created successfully.")
    else:
        print(
            f"Failed to create alert rule '{alert_rule.title}'. Response: {response.text}"
        )


def delete_alert_rule(rule_uid: str, title: str) -> None:
    response = requests.delete(
        f"{GRAFANA_URL}/api/v1/provisioning/alert-rules/{rule_uid}", headers=HEADERS
    )
    if response.status_code == 204:
        print(f"Alert rule with UID '{rule_uid}' title {title} deleted successfully.")
    else:
        print(
            f"Failed to delete alert rule with UID '{rule_uid}'. Response: {response.text}"
        )


def update_alert_rule(rule_uid: str, alert_rule: NormalizedAlertRule) -> None:
    payload = alert_rule.to_payload()
    response = requests.put(
        f"{GRAFANA_URL}/api/v1/provisioning/alert-rules/{rule_uid}",
        json=payload,
        headers=HEADERS,
    )
    if response.status_code == 200:
        print(f"Alert rule '{alert_rule.title}' updated successfully.")
    else:
        print(
            f"Failed to update alert rule '{alert_rule.title}'. Response: {response.text}"
        )


if __name__ == "__main__":
    current_rules = fetch_grafana_alert_rules()
    normalized_current_rules = normalize_alert_rules(current_rules)
    print("Current Alerts:")
    for rule in current_rules:
        print(rule)
    print("Normalized Alerts:")
    for rule in normalized_current_rules:
        print(rule)
