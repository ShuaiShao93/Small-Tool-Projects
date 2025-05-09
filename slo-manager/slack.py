import json
import os
from typing import Set, Tuple

import requests

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL_NAME = "#slo-alerts"


def send_missing_slo_warning(missing_method_paths: Set[Tuple[str, str]]) -> None:
    assert SLACK_BOT_TOKEN, "SLACK_BOT_TOKEN environment variable is not set"

    if not missing_method_paths:
        return

    slo_list = "\n".join(
        [f"• *{method}*: {path}" for method, path in missing_method_paths]
    )
    message = f":warning: *Missing SLO Detected* :warning:\nThe following SLOs are missing, please follow the README to add:\n{slo_list}"

    payload = {
        "channel": SLACK_CHANNEL_NAME,
        "text": message,
        "mrkdwn": True,  # Enables Markdown formatting in the message
    }

    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload),
    )

    # Check the response
    if response.status_code == 200:
        response_data = response.json()
        if response_data.get("ok"):
            print(f"Message sent successfully to {SLACK_CHANNEL_NAME}.")
        else:
            print(f"Error sending message: {response_data.get('error')}")
    else:
        print(f"HTTP Error: {response.status_code} - {response.reason}")
