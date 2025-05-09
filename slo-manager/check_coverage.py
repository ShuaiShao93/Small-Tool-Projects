import os
import re
import time
from typing import Set, Tuple, Union

import requests

from python.config_parser import (
    CLUSTER_NAMES,
    get_method_path_combinations,
    load_all_api_group_slos,
)
from python.grafana import HEADERS
from python.slack import send_missing_slo_warning

PROMETHEUS_URL = "https://prometheus-prod-36-prod-us-west-0.grafana.net/api/prom"

GRAFANA_CLOUD_PROM_USERNAME = os.environ.get("GRAFANA_CLOUD_PROM_USERNAME")
GRAFANA_CLOUD_PROM_PASSWORD = os.environ.get("GRAFANA_CLOUD_PROM_PASSWORD")

QUERY_WINDOW_SECONDS = 60 * 60 * 24  # 24 hours


def get_method_path_combinations_from_metrics() -> Set[Tuple[str, str]]:
    assert (
        GRAFANA_CLOUD_PROM_USERNAME
    ), "GRAFANA_CLOUD_PROM_USERNAME environment variable is not set"
    assert (
        GRAFANA_CLOUD_PROM_PASSWORD
    ), "GRAFANA_CLOUD_PROM_PASSWORD environment variable is not set"

    cluster_names = "|".join(CLUSTER_NAMES)
    params: dict[str, Union[str, int]] = {
        "match[]": f'api_request_duration_seconds_bucket{{origin_prometheus=~"{cluster_names}"}}',
        "start": int(time.time()) - QUERY_WINDOW_SECONDS,
        "end": int(time.time()),
    }

    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/series",
        headers=HEADERS,
        params=params,
        auth=(GRAFANA_CLOUD_PROM_USERNAME, GRAFANA_CLOUD_PROM_PASSWORD),
    )

    label_combinations = set()
    if response.status_code == 200:
        series_data = response.json().get("data", [])

        for series in series_data:
            method = series.get("method")
            path = series.get("path")
            if method and path:
                label_combinations.add((method, path))

        print(
            f"Unique method-path combinations in the last 24 hours: {len(label_combinations)}"
        )
    else:
        print(f"Error fetching data: {response.status_code} - {response.reason}")

    return label_combinations


def get_missing_method_paths(
    slo_method_path_combinations: Set[Tuple[str, str]],
    prometheus_method_paths: Set[Tuple[str, str]],
) -> Set[Tuple[str, str]]:
    missing = set()

    slo_patterns = []
    for method, path_regex in slo_method_path_combinations:
        slo_patterns.append(
            (method.upper(), re.compile(f"^{path_regex.rstrip('/')}/?$"))
        )

    for method, path in prometheus_method_paths:
        normalized_path = path.rstrip("/")
        method_upper = method.upper()
        matched = False

        for slo_method, slo_path_pattern in slo_patterns:
            if method_upper == slo_method and slo_path_pattern.match(normalized_path):
                matched = True
                break

        if not matched:
            missing.add((method_upper, normalized_path))

    return missing


if __name__ == "__main__":
    api_group_slos = load_all_api_group_slos()
    slo_method_path_combinations = get_method_path_combinations(api_group_slos)

    prometheus_method_paths = get_method_path_combinations_from_metrics()

    missing_method_paths = get_missing_method_paths(
        slo_method_path_combinations, prometheus_method_paths
    )
    if missing_method_paths:
        print(
            f"Missing method-path combinations in alert rules: {missing_method_paths}, sending to slack"
        )
        send_missing_slo_warning(missing_method_paths)
