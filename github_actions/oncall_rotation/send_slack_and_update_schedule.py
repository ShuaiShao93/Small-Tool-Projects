import datetime
import os
import yaml
import requests

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

SLACK_CHANNEL_ID_MAP = {
    "channelA": "ID_A",
    "channelB": "ID_B",
}

SLACK_NAME_ID_MAP = {
    "A": "ID_A",
    "B": "ID_B",
}

ONCALL_SCHEDULE = "oncall_schedule.yaml"

def send_current_oncall():
    with open(ONCALL_SCHEDULE) as f:
        schedule = yaml.safe_load(f)

    # Determine the current on-call user
    today = datetime.datetime.now().date()
    current_primary = None
    topic_message = None
    for entry in schedule:
        start = datetime.datetime.strptime(entry["start"], "%m-%d-%Y").date()
        end = datetime.datetime.strptime(entry["end"], "%m-%d-%Y").date()
        if start <= today <= end:
            current_primary = entry["primary"]
            current_secondary = entry["secondary"]
            topic_message = f"This week's on-call: primary: @{current_primary} secondary: @{current_secondary}"
            print(topic_message)
            break

    if not current_primary:
        raise ValueError("No on-call user found for today")

    # Update the Slack channel topic
    url = "https://slack.com/api/conversations.setTopic"
    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}

    for channel, channel_id in SLACK_CHANNEL_ID_MAP.items():
        data = {
            "channel": channel_id,
            "topic": topic_message
        }
        response = requests.post(url, headers=headers, data=data)
        print("Slack API response:", response.json())
    
def update_schedule():
    with open(ONCALL_SCHEDULE) as f:
        schedule = yaml.safe_load(f)

    new_entries = []
    today = datetime.datetime.now().date()
    last_end_date = datetime.datetime.strptime(schedule[-1]["end"], "%m-%d-%Y").date()

    # Remove outdated entries and add new entries.
    for entry in schedule[:]:
        end = datetime.datetime.strptime(entry["end"], "%m-%d-%Y").date()
        if end < today:
            new_start_date = last_end_date + datetime.timedelta(days=1)
            new_end_date = last_end_date + datetime.timedelta(weeks=2)
            
            new_entry = {
                "start": new_start_date.strftime("%m-%d-%Y"),
                "end": new_end_date.strftime("%m-%d-%Y"),
                "primary": entry["primary"],
                "secondary": entry["secondary"]
            }
            
            new_entries.append(new_entry)
            schedule.remove(entry)
            last_end_date = new_end_date

    schedule.extend(new_entries)
    schedule.sort(key=lambda x: datetime.datetime.strptime(x["start"], "%m-%d-%Y"))

    with open(ONCALL_SCHEDULE, "w") as f:
        yaml.safe_dump(schedule, f, default_flow_style=False, sort_keys=False)

if __name__ == "__main__":
    update_schedule()
    send_current_oncall()
