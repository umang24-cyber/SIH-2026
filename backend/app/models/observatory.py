"""Public, chart-ready contracts for the offline model/data Observatory."""
from typing import Annotated, Generic, Literal, TypeVar

from pydantic import BaseModel, Field, model_validator

Score = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
Count = Annotated[int, Field(ge=0)]
T = TypeVar("T")


class ObservatoryMeta(BaseModel):
    sources: list[str]
    scope: str
    dataset_version: str | None = None
    model_version: str | None = None
    synthetic: bool = True
    generated_at: str
    notes: list[str] = Field(default_factory=list)


class ObservatoryResponse(BaseModel, Generic[T]):
    schema_version: Literal["1.0"] = "1.0"
    status: Literal["available", "unavailable"]
    meta: ObservatoryMeta
    data: T | None
    message: str | None = None


class CountItem(BaseModel):
    id: str
    label: str
    count: Count


class DatasetSplit(BaseModel):
    id: str
    label: str
    transactions: Count
    scenarios: Count


class DatasetTotals(BaseModel):
    transactions: Count
    scenarios: Count
    unique_wallets: Count
    first_timestamp: str
    last_timestamp: str


class TimelinePoint(BaseModel):
    timestamp: str
    transactions: Count
    output_volume_btc: Annotated[float, Field(ge=0, allow_inf_nan=False)]


class DatasetData(BaseModel):
    totals: DatasetTotals
    splits: list[DatasetSplit]
    bucket: Literal["day", "week", "month"]
    timezone: Literal["UTC"] = "UTC"
    timeline: list[TimelinePoint]
    scenario_class_distribution: list[CountItem]
    scenario_binary_distribution: list[CountItem]
    transaction_class_distribution: list[CountItem]
    infrastructure_distribution: list[CountItem]
    country_distribution: list[CountItem]
    script_distribution: list[CountItem]


class Metric(BaseModel):
    id: str
    label: str
    value: Score
    unit: Literal["ratio"] = "ratio"


class ConfusionMatrix(BaseModel):
    labels: list[str]
    values: list[list[Count]]
    row_axis: Literal["actual"] = "actual"
    column_axis: Literal["predicted"] = "predicted"

    @model_validator(mode="after")
    def square_matrix(self):
        n = len(self.labels)
        if not n or len(set(self.labels)) != n or len(self.values) != n:
            raise ValueError("Confusion matrix labels and rows must match")
        if any(len(row) != n for row in self.values):
            raise ValueError("Confusion matrix must be square")
        return self


class ClassMetrics(BaseModel):
    id: str
    label: str
    precision: Score
    recall: Score
    f1: Score
    support: Count
    predicted_count: Count


class ModelPerformance(BaseModel):
    sample_count: Count
    metrics: list[Metric]
    confusion_matrix: ConfusionMatrix | None = None
    per_class: list[ClassMetrics] = Field(default_factory=list)


class Diagnostic(BaseModel):
    id: str
    label: str
    metrics: list[Metric]
    note: str


class PerformanceData(BaseModel):
    evaluation_date: str
    evaluation_type: str
    scoring_unit: Literal["scenario"] = "scenario"
    threshold: Score
    binary: ModelPerformance
    typology: ModelPerformance
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    formal_decision: str | None = None
    limitations: list[str]
    curves_available: Literal[False] = False
    curves_unavailable_reason: str


class OverviewData(BaseModel):
    title: str
    model_role: Literal["offline_benchmark"] = "offline_benchmark"
    evaluation_date: str
    transactions: Count
    scenarios: Count
    train_scenarios: Count
    test_scenarios: Count
    features: Count
    binary_model: str
    typology_model: str
    headline_metrics: list[Metric]
    formal_decision: str | None = None
    sections: list[str]


class FeatureItem(BaseModel):
    id: str
    label: str
    group: str
    importance: Score


class FeatureData(BaseModel):
    model: Literal["binary", "typology"]
    method: Literal["normalized_xgboost_gain"] = "normalized_xgboost_gain"
    description: str
    feature_count: Count
    features: list[FeatureItem]
    groups: list[FeatureItem]
    local_shap_available: Literal[False] = False
    local_shap_unavailable_reason: str


class DiagramNode(BaseModel):
    id: str
    label: str
    description: str


class DiagramEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str


class Diagram(BaseModel):
    id: str
    label: str
    kind: Literal["architecture", "illustration"]
    description: str
    nodes: list[DiagramNode]
    edges: list[DiagramEdge]


class PatternsData(BaseModel):
    patterns: list[Diagram]
