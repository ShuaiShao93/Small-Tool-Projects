import os
from typing import List, Set, Tuple

import yaml

from python.models import (
    AlertReceiver,
    ApiGroupSlo,
    NormalizedAlertRule,
    NormalizedAlertRuleAnnotations,
    NormalizedAlertRuleData,
    NormalizedAlertRuleModelA,
    NormalizedAlertRuleModelC,
)

CLUSTER_NAMES = ["galileo-v2"]
RATE_WINDOW = "60m"


def single_latency_slo_to_alert_rule(
    group: ApiGroupSlo, percentile: int, latency_ms: int
) -> NormalizedAlertRule:
    paths = "|".join([endpoint.path for endpoint in group.endpoints])
    methods = "|".join(group.methods)
    cluster_names = "|".join(CLUSTER_NAMES)
    data = [
        NormalizedAlertRuleData(
            refId="A",
            datasourceUid="grafanacloud-prom",
            relativeTimeRange={"from": 600, "to": 0},
            model=NormalizedAlertRuleModelA(
                expr=f'histogram_quantile({percentile / 100}, sum by(le, origin_prometheus, path, method) (rate(api_request_duration_seconds_bucket{{path=~"{paths}", origin_prometheus=~"{cluster_names}", method=~"{methods}"}}[{RATE_WINDOW}]))) * 1000',
            ),
        ),
        NormalizedAlertRuleData(
            refId="C",
            datasourceUid="__expr__",
            relativeTimeRange={"from": 0, "to": 0},
            model=NormalizedAlertRuleModelC(
                conditions=[
                    {
                        "evaluator": {"params": [latency_ms], "type": "gt"},
                        "operator": {"type": "and"},
                        "query": {"params": ["C"]},
                        "reducer": {"params": [], "type": "last"},
                        "type": "query",
                    }
                ],
            ),
        ),
    ]
    alert_rule = NormalizedAlertRule(
        title=group.name + f" P{percentile} latency",
        ruleGroup="API Latency",
        data=data,
        condition="C",
        noDataState="KeepLast",
        execErrState="KeepLast",
        pending_for="5m",
        keep_firing_for="0s",
        annotations=NormalizedAlertRuleAnnotations(
            summary=f"API P{percentile} Latency SLO Breach for group '{group.name}'",
            description='Customer {{ index $labels "origin_prometheus" }}\nMethod {{ index $labels "method" }}\nPath {{ index $labels "path" }}',
        ),
        labels={
            "og_priority": "P1",
        },
        notification_settings={"receiver": "slo-slack"}
        if group.alert_receiver == AlertReceiver.DEV_SLACK
        else None,
    )
    return alert_rule


def group_slo_to_alert_rules(group_slo: ApiGroupSlo) -> List[NormalizedAlertRule]:
    if not group_slo.slo:
        return []
    return [
        single_latency_slo_to_alert_rule(group_slo, 50, group_slo.slo.p50_latency_ms),
        single_latency_slo_to_alert_rule(group_slo, 99, group_slo.slo.p99_latency_ms),
    ]


def load_all_api_group_slos() -> List[ApiGroupSlo]:
    dup_names = set()
    slo_names = set()
    api_group_slos = []
    for root, _, files in os.walk("config/api"):
        for file_name in files:
            if file_name.endswith(".yaml"):
                file_path = os.path.join(root, file_name)
                with open(file_path, "r") as file:
                    config = yaml.safe_load(file)
                    for group in config:
                        group_slo = ApiGroupSlo(**group)
                        if group_slo.name in slo_names:
                            dup_names.add(group_slo.name)
                        slo_names.add(group_slo.name)
                        api_group_slos.append(group_slo)

    if dup_names:
        error_list = "\n".join(
            f"{i}. {name}" for i, name in enumerate(dup_names, start=1)
        )
        raise ValueError(f"Following duplicate SLO group name found:\n{error_list}")

    # Check for duplicate method-path combinations.
    get_method_path_combinations(api_group_slos)
    return sorted(api_group_slos, key=lambda x: x.name)


def load_all_pending_alert_rules() -> List[NormalizedAlertRule]:
    """Load all pending alert rules from the config directory."""
    pending_alerts = []
    api_group_slos = load_all_api_group_slos()
    for group_slo in api_group_slos:
        pending_alerts.extend(group_slo_to_alert_rules(group_slo))

    return sorted(pending_alerts, key=lambda x: x.title)


def get_method_path_combinations(
    api_group_slos: List[ApiGroupSlo],
) -> Set[Tuple[str, str]]:
    """Also check for duplicate method-path combinations in the current alert rules."""
    dup_path_combinations = set()
    method_path_combinations = set()
    for group_slo in api_group_slos:
        for endpoint in group_slo.endpoints:
            for method in group_slo.methods:
                key = (method, endpoint.path)
                if key in method_path_combinations:
                    dup_path_combinations.add(key)
                method_path_combinations.add(key)

    if dup_path_combinations:
        error_list = "\n".join(
            f"{i}. {key}" for i, key in enumerate(dup_path_combinations, start=1)
        )
        raise ValueError(
            f"Following duplicate method-path combination found:\n{error_list}"
        )
    return method_path_combinations


if __name__ == "__main__":
    all_alerts = load_all_pending_alert_rules()
    print("Pending Alerts:")
    for alert in all_alerts:
        print(alert)
