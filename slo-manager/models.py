import enum
from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict

CLUSTER_NAMES = ["CLUSTER"]
RATE_WINDOW = "60m"


class Endpoint(BaseModel):
    path: str


class Slo(BaseModel):
    p50_latency_ms: int
    p99_latency_ms: int


class AlertReceiver(enum.Enum):
    DEV_SLACK = "dev_slack"  # slo-alerts channel
    PROD = "prod"  # on-call


class ApiGroupSlo(BaseModel):
    name: str
    methods: List[str]
    endpoints: List[Endpoint]
    slo: Optional[Slo] = None
    alert_receiver: AlertReceiver


class NormalizedAlertRuleModelA(BaseModel):
    model_config = ConfigDict(extra="ignore")

    editorMode: str = "builder"
    expr: str
    instant: bool = True
    range: bool = False
    refId: str = "A"

    def __str__(self) -> str:
        return f"expr: {self.expr}"


class NormalizedAlertRuleModelC(BaseModel):
    model_config = ConfigDict(extra="ignore")

    conditions: List[dict]
    datasource: dict = {"type": "__expr__", "uid": "__expr__"}
    expression: str = "A"
    refId: str = "C"
    type: str = "threshold"

    def __str__(self) -> str:
        return f"evaluator: {self.conditions[0]['evaluator']}"


class NormalizedAlertRuleData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    refId: str
    relativeTimeRange: dict
    datasourceUid: str
    model: Union[NormalizedAlertRuleModelA, NormalizedAlertRuleModelC]

    def __str__(self) -> str:
        return str(self.model)


class NormalizedAlertRuleAnnotations(BaseModel):
    description: str
    summary: str


class NormalizedAlertRule(BaseModel):
    orgID: int = 1
    folderUID: str = "aed99410-b895-44c6-b7eb-02d071ca45ee"
    ruleGroup: str
    title: str
    condition: str
    data: List[NormalizedAlertRuleData]
    noDataState: str
    execErrState: str
    pending_for: str
    keep_firing_for: str
    annotations: NormalizedAlertRuleAnnotations
    labels: Optional[dict] = None
    notification_settings: Optional[dict] = None

    def to_payload(self) -> dict:
        payload = self.model_dump()
        payload["for"] = payload["pending_for"]
        del payload["pending_for"]
        return payload

    @classmethod
    def from_grafana_rule(cls, grafana_rule: dict) -> "NormalizedAlertRule":
        """
        Create a NormalizedAlertRule instance from a Grafana rule dictionary.
        """
        grafana_rule["pending_for"] = grafana_rule.pop("for")
        return cls(**grafana_rule)

    def __str__(self) -> str:
        lines = []
        lines.append(f"Title: {self.title}")
        lines.append(f"Rule Group: {self.ruleGroup}")
        lines.append(f"Summary: {self.annotations.summary}")
        lines.append(f"Description: {self.annotations.description}")
        lines.append("Data:")
        for data in self.data:
            lines.append(f"  - {data}")
        lines.append(f"Notification Settings: {self.notification_settings}")
        lines.append(f"Labels: {self.labels}")
        return "\n".join(lines)
