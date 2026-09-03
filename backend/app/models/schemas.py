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
# 2. Entity / Wallet Schemas
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
# 5. Multi-Hop Trace Schemas
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

# ==========================================
# 6. Alert & Explainable Evidence Schemas
# ==========================================

class AlertSummary(BaseModel):
    candidate_id: str
    scenario_id: str
    predicted_pattern_type: str
    confidence: float
    severity: str = Field(description="CRITICAL, HIGH, MEDIUM, LOW")
    explanation: str
    primary_wallet: str
    member_txids: List[int]
    member_wallets: List[str]
    detected_at: str

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
    confidence: float
    typology_heuristic_match: Dict[str, Any]
    ml_feature_attributions: List[FeatureAttribution]
    telemetry_summary: Dict[str, Any]
    transactions: List[Dict[str, Any]]
