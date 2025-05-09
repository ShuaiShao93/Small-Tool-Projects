from python.config_parser import load_all_pending_alert_rules
from python.diff_pending_and_current_rules import calculate_rule_changes
from python.grafana import (
    create_alert_rule,
    delete_alert_rule,
    fetch_grafana_alert_rules,
    get_title_to_uid_map,
    normalize_alert_rules,
    update_alert_rule,
)

if __name__ == "__main__":
    pending_rules = load_all_pending_alert_rules()
    grafana_alert_rules = fetch_grafana_alert_rules()
    title_to_id = get_title_to_uid_map(grafana_alert_rules)
    current_rules = normalize_alert_rules(grafana_alert_rules)

    rules_to_add, rules_to_update, rules_to_delete = calculate_rule_changes(
        current_rules, pending_rules
    )
    if not rules_to_add and not rules_to_update and not rules_to_delete:
        print("No changes detected.")

    for rule in rules_to_delete:
        assert rule.title in title_to_id, f"Rule {rule.title} not found in Grafana"
        delete_alert_rule(title_to_id[rule.title], rule.title)

    for rule in rules_to_add:
        create_alert_rule(rule)

    for rule in rules_to_update:
        assert rule.title in title_to_id, f"Rule {rule.title} not found in Grafana"
        update_alert_rule(title_to_id[rule.title], rule)
