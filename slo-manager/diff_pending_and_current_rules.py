import difflib
from typing import List, Tuple

from python.config_parser import load_all_pending_alert_rules
from python.grafana import fetch_grafana_alert_rules, normalize_alert_rules
from python.models import NormalizedAlertRule


def calculate_rule_changes(
    current_rules: List[NormalizedAlertRule], new_rules: List[NormalizedAlertRule]
) -> Tuple[
    List[NormalizedAlertRule], List[NormalizedAlertRule], List[NormalizedAlertRule]
]:
    """
    Calculate the differences between current rules and new rules.
    Returns a tuple of lists:
    - rules_to_add: Rules that are in new_rules but not in current_rules
    - rules_to_update: Rules that are in both but have different attributes
    - rules_to_delete: Rules that are in current_rules but not in new_rules
    """
    rules_to_add = []
    rules_to_update = []
    rules_to_delete = []
    current_rule_title_to_rule = {rule.title: rule for rule in current_rules}
    new_rule_title_to_rule = {rule.title: rule for rule in new_rules}
    # Rules to add
    for title, new_rule in new_rule_title_to_rule.items():
        if title not in current_rule_title_to_rule:
            rules_to_add.append(new_rule)
        else:
            current_rule = current_rule_title_to_rule[title]
            if current_rule != new_rule:
                rules_to_update.append(new_rule)
    # Rules to delete
    for title, current_rule in current_rule_title_to_rule.items():
        if title not in new_rule_title_to_rule:
            rules_to_delete.append(current_rule)

    return rules_to_add, rules_to_update, rules_to_delete


def diff_rules(
    current_rules: List[NormalizedAlertRule], new_rules: List[NormalizedAlertRule]
) -> str:
    current_rules_str = "\n\n".join([str(rule) for rule in current_rules])
    new_rules_str = "\n\n".join([str(rule) for rule in new_rules])
    diff = difflib.unified_diff(
        current_rules_str.splitlines(),
        new_rules_str.splitlines(),
        fromfile="Current Rules",
        tofile="New Rules",
        lineterm="",
    )
    diff_str = "\n".join(diff)
    if diff_str:
        diff_str = "```diff\n" + diff_str + "\n```"
    return diff_str


def main() -> None:
    pending_rules = load_all_pending_alert_rules()
    grafana_alert_rules = fetch_grafana_alert_rules()
    current_rules = normalize_alert_rules(grafana_alert_rules)

    diff_str = diff_rules(current_rules, pending_rules)
    print(diff_str)


if __name__ == "__main__":
    main()
