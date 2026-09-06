"""
Pydantic v2 Response and Request Schemas.
Directly implements all endpoint specifications in docs/API_CONTRACT.md.
"""
from typing import Any, Optional, List, Dict
from pydantic import BaseModel, Field

# ==========================================
# 1. System Health & Metadata
# ==========================================

class HealthResponse(BaseModel):
    status: str = "ONLINE"
    app_name: str
    version: str
    loaded_transactions: int
    unique_scenarios: int
    unique_wallets: int
    uptime_seconds: float

# ==========================================
# 2. Entity / Wallet & Clustering Schemas
# ==========================================

class EntityResponse(BaseModel):
    address: str
    is_licit_exchange: bool = False
    total_received_btc: float
    total_sent_btc: float
    tx_count: int
    first_seen: str
    last_seen: str
    associated_scenarios: List[str]

class ClusterResponse(BaseModel):
    query_address: str
    cluster_id: str
    cluster_size: int
    co_owned_addresses: List[str]
    total_cluster_received_btc: float
    total_cluster_sent_btc: float
    multi_input_tx_count: int
    associated_scenarios: List[str]

# ==========================================
# 3. Transaction Schemas
# ==========================================

class NetworkTelemetry(BaseModel):
    relay_timestamp: str
    relay_ip: str
    relay_port: int
    node_type: str
    country_code: str
    asn: str
    isp: str
    protocol_version: int = 70015
    user_agent: str
    propagation_delta_ms: float

class TransactionResponse(BaseModel):
    txid: int
    timestamp: str
    input_addresses: List[str]
    output_addresses: List[str]
    input_amounts: List[float]
    output_amounts: List[float]
    fee_btc: float
    script_type: str
    scenario_id: str
    network: NetworkTelemetry

# ==========================================
# 4. Graph Schemas (Wallet / Tx / IP Nodes)
# ==========================================

class GraphNode(BaseModel):
    id: str
    type: str = Field(description="Node type: Wallet, Transaction, or IP")
    properties: Dict[str, Any]

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str = Field(description="Edge type: SENT, RECEIVED, or BROADCAST")
    properties: Dict[str, Any]

class GraphResponse(BaseModel):
    scenario_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]

# ==========================================
# 5. Multi-Hop Trace & Taint Analysis Schemas
# ==========================================

class TraceHop(BaseModel):
    hop_index: int
    from_wallet: str
    to_wallet: str
    txid: int
    amount_btc: float
    timestamp: str
    flagged_typology: Optional[str] = None

class TraceResponse(BaseModel):
    source_address: str
    destination_address: str
    path_found: bool
    hop_count: int
    total_transferred_btc: float
    hops: List[TraceHop]

class TaintNode(BaseModel):
    address: str
    hop_distance: int
    taint_score: float = Field(description="Contamination level between 0.0 and 1.0")
    received_btc_from_seed: float
    via_txid: int
    is_licit_exchange: bool = False
    received_tainted_btc: Optional[float] = None

    def model_post_init(self, __context):
        if self.received_tainted_btc is None:
            self.received_tainted_btc = self.received_btc_from_seed

class TaintResponse(BaseModel):
    seed_address: str
    decay_rate: float
    max_depth: int
    total_tainted_wallets: int
    total_tainted_volume_btc: float
    contaminated_wallets: List[TaintNode]
    total_tainted_btc: Optional[float] = None
    tainted_descendants: Optional[List[TaintNode]] = None

    def model_post_init(self, __context):
        if self.total_tainted_btc is None:
            self.total_tainted_btc = self.total_tainted_volume_btc
        if self.tainted_descendants is None:
            self.tainted_descendants = self.contaminated_wallets

# ==========================================
# 5b. Anomaly Detection Schema (Isolation Forest)
#     Separate from all XGBoost outputs.
# ==========================================

class AnomalyScoreResponse(BaseModel):
    """
    Isolation Forest Anomaly/Unusualness Score.
    NOT a probability. NOT combined with risk_score or typology_confidence.
    Score 0 = indistinguishable from normal licit activity.
    Score 100 = maximally anomalous relative to licit reference distribution.
    """
    scenario_id: str
    anomaly_score: float = Field(
        description="0–100 Anomaly/Unusualness Score. Higher = more anomalous."
    )
    anomaly_label: str = Field(
        description="HIGH (>=70), MEDIUM (>=40), or LOW (<40)."
    )
    anomaly_raw_if_score: float = Field(
        description="Raw IsolationForest score_samples() output before normalization."
    )
    anomaly_high_threshold: float = Field(
        default=70.0,
        description="Threshold above which anomaly_label is HIGH."
    )
    anomaly_interpretation: str = Field(
        description="Human-readable explanation of what this score represents."
    )

# ==========================================
# 6. Alert & Explainable Evidence Schemas
# ==========================================

class AlertSummary(BaseModel):
    candidate_id: str
    scenario_id: str
    predicted_pattern_type: str
    binary_confidence: float = Field(
        description="Binary XGBoost probability for the predicted is_illicit class."
    )
    typology_confidence: float = Field(
        description="Top-class probability from the typology XGBoost model."
    )
    severity: str = Field(description="CRITICAL, HIGH, MEDIUM, LOW")
    explanation: str
    primary_wallet: str
    member_txids: List[int]
    member_wallets: List[str]
    detected_at: str
    is_ml_driven: bool = Field(
        default=True,
        description="True when label and confidence fields come from the ML model, not a hardcoded heuristic."
    )
    risk_score: float = Field(default=0.0, description="Binary model P(illicit) score from 0–1.")

class AlertListResponse(BaseModel):
    total_alerts: int
    alerts: List[AlertSummary]

class FeatureAttribution(BaseModel):
    feature_name: str
    value: Any
    shap_value: float
    direction: str = Field(description="RISK_INCREASING or RISK_DECREASING")

class EvidenceResponse(BaseModel):
    candidate_id: str
    scenario_id: str
    predicted_pattern_type: str
    binary_confidence: float = Field(
        description="Binary XGBoost probability for the predicted is_illicit class."
    )
    typology_confidence: float = Field(
        description="Top-class probability from the typology XGBoost model."
    )
    typology_heuristic_match: Dict[str, Any]
    # Binary model SHAP attributions (kept for backwards compatibility)
    ml_feature_attributions: List[FeatureAttribution]
    # Typology model SHAP attributions for the predicted class
    typology_shap_attributions: List[FeatureAttribution] = Field(default_factory=list)
    # Human-readable explanation generated from typology SHAP
    typology_explanation: str = ""
    telemetry_summary: Dict[str, Any]
    transactions: List[Dict[str, Any]]

# ==========================================
# 7. Live Dynamic Ingestion Schemas
# ==========================================

class IngestTransactionRequest(BaseModel):
    txid: int
    timestamp: str
    input_addresses: List[str]
    output_addresses: List[str]
    input_amounts: List[float]
    output_amounts: List[float]
    fee_btc: float = 0.0001
    script_type: str = "P2PKH"
    scenario_id: Optional[str] = None
    # Network Layer Telemetry (correlated observation)
    relay_timestamp: Optional[str] = None
    relay_ip: Optional[str] = "127.0.0.1"
    relay_port: Optional[int] = 8333
    node_type: Optional[str] = "residential"
    country_code: Optional[str] = "US"
    asn: Optional[str] = "AS15169"
    isp: Optional[str] = "Standard ISP"
    user_agent: Optional[str] = "/Satoshi:22.0.0/"
    propagation_delta_ms: Optional[float] = None

class IngestResultResponse(BaseModel):
    status: str = "SUCCESS"
    message: str
    txid: int
    scenario_id: str
    primary_wallet: str
    risk_score: float
    is_illicit: bool
    binary_confidence: float
    predicted_typology: str
    typology_confidence: float
    anomaly_score: Optional[float] = None
    anomaly_label: Optional[str] = None
    top_shap_attributions: List[FeatureAttribution] = Field(default_factory=list)
    dossier_available: bool = True

class IngestBatchResponse(BaseModel):
    status: str = "SUCCESS"
    total_ingested: int
    scenario_ids: List[str]
    unique_wallets_added: int
    sample_txids: List[int]
    message: str
