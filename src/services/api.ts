/**
 * Centralized Typed API Client for BitKaun Forensic Backend (FastAPI).
 * 100% Offline / Air-Gapped compliant.
 */

const BASE_URL = '';

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = endpoint.startsWith('/') ? `${BASE_URL}${endpoint}` : `${BASE_URL}/${endpoint}`;
  const isFormData = typeof FormData !== 'undefined' && options?.body instanceof FormData;
  const headers: Record<string, string> = {
    ...(!isFormData ? { 'Content-Type': 'application/json' } : {}),
    ...(options?.headers as Record<string, string>),
  };
  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorDetail = response.statusText;
    try {
      const errJson = JSON.parse(errorText);
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      errorDetail = errorText || errorDetail;
    }
    throw new Error(`API Error [${response.status}]: ${errorDetail}`);
  }

  return response.json();
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  loaded_transactions: number;
  unique_scenarios: number;
  unique_wallets: number;
  uptime_seconds: number;
  alert_count: number;
  cluster_count: number;
  illicit_transaction_ratio?: number | null;
  illicit_ratio_note: string;
}

export interface EntityResponse {
  address: string;
  is_licit_exchange: boolean;
  total_received_btc: number;
  total_sent_btc: number;
  tx_count: number;
  first_seen: string;
  last_seen: string;
  associated_scenarios: string[];
}

export interface ClusterResponse {
  query_address: string;
  cluster_id: string;
  cluster_size: number;
  co_owned_addresses: string[];
  total_cluster_received_btc: number;
  total_cluster_sent_btc: number;
  multi_input_tx_count: number;
  associated_scenarios: string[];
}

export interface NetworkTelemetry {
  relay_timestamp: string;
  relay_ip: string;
  relay_port: number;
  node_type: string;
  country_code: string;
  asn: string;
  isp: string;
  protocol_version: number;
  user_agent: string;
  propagation_delta_ms: number;
}

export interface TransactionResponse {
  txid: number;
  timestamp: string;
  input_addresses: string[];
  output_addresses: string[];
  input_amounts: number[];
  output_amounts: number[];
  fee_btc: number;
  script_type: string;
  scenario_id: string;
  network: NetworkTelemetry;
}

export interface TraceHop {
  hop_index: number;
  from_wallet: string;
  to_wallet: string;
  txid: number;
  amount_btc: number;
  timestamp: string;
  flagged_typology?: string | null;
}

export interface TraceResponse {
  source_address: string;
  destination_address: string;
  path_found: boolean;
  hop_count: number;
  total_transferred_btc: number;
  hops: TraceHop[];
}

export interface IngestScenarioAnalysis {
  scenario_id: string;
  transaction_count: number;
  analysis_status: 'AVAILABLE' | 'UNAVAILABLE';
  analysis_message: string;
  feature_count: number;
  score_scope: 'SCENARIO';
  sample_size_warning?: string | null;
  risk_score?: number | null;
  is_illicit?: boolean | null;
  binary_confidence?: number | null;
  predicted_typology?: string | null;
  typology_confidence?: number | null;
  typology_explanation: string;
  anomaly_score?: number | null;
  anomaly_label?: string | null;
  anomaly_message: string;
  top_shap_attributions: Array<{
    feature_name: string;
    value: number | string;
    shap_value: number;
    direction: string;
  }>;
  typology_shap_attributions: Array<{
    feature_name: string;
    value: number | string;
    shap_value: number;
    direction: string;
  }>;
}

export interface TaintNode {
  address: string;
  taint_score: number;
  hop_distance: number;
  received_tainted_btc: number;
  via_txid: number;
}

export interface TaintResponse {
  seed_address: string;
  decay_rate: number;
  max_depth: number;
  total_tainted_wallets: number;
  total_tainted_volume_btc: number;
  contaminated_wallets: TaintNode[];
}

export interface AlertSummary {
  candidate_id: string;
  scenario_id: string;
  predicted_pattern_type: string;
  binary_confidence: number;
  typology_confidence: number;
  severity: string;
  explanation: string;
  primary_wallet: string;
  member_txids: number[];
  member_wallets: string[];
  detected_at: string;
  is_ml_driven?: boolean;
  risk_score?: number;
  anomaly_score?: number;
  anomaly_label?: string;
}

export interface FeatureAttribution {
  feature_name: string;
  value: any;
  shap_value: number;
  direction: string;
}

export interface EvidenceResponse {
  candidate_id: string;
  scenario_id: string;
  predicted_pattern_type: string;
  binary_confidence: number;
  typology_confidence: number;
  typology_heuristic_match?: Record<string, any>;
  ml_feature_attributions: FeatureAttribution[];
  typology_shap_attributions: FeatureAttribution[];
  typology_explanation: string;
  telemetry_summary: {
    origin_ips?: string[];
    origin_asns?: string[];
    countries?: string[];
    infrastructure_distribution?: Record<string, number>;
  };
  transactions?: any[];
}

export interface ScenarioGraph {
  scenario_id: string;
  node_count: number;
  edge_count: number;
  nodes: {
    id: string;
    type: 'Wallet' | 'Transaction' | 'IP';
    label: string;
    properties: Record<string, any>;
  }[];
  edges: {
    id: string;
    source: string;
    target: string;
    type: 'SENT' | 'RECEIVED' | 'BROADCAST';
    amount_btc?: number;
    relay_timestamp?: string;
  }[];
}

export interface DossierResponse {
  case_metadata: {
    dossier_id: string;
    generation_timestamp: string;
    document_owner: string;
    legal_context: string;
    document_status: string;
    data_status: string;
    model_status: string;
  };
  transaction_evidence: {
    txid: number;
    timestamp_utc: string;
    transferred_btc: number;
    fee_btc: number;
    input_addresses: string[];
    output_addresses: string[];
  };
  network_telemetry_observation: {
    observed_relay_ip: string;
    recorded_isp: string;
    recorded_asn: string;
    recorded_country_code: string;
    tor_exit_indicator: boolean;
    propagation_delta_t_seconds: number;
  };
  entity_clustering: {
    entity_cluster_id: string;
    total_cioh_linked_addresses_observed: number;
    sample_co_owned_addresses: string[];
  };
  threat_assessment: {
    composite_risk_score: number;
    risk_rating: string;
    detected_typologies: string[];
    taint_hop_flows_count: number;
  };
  recommended_investigative_actions: string[];
}

export interface TorSummary {
  total_tor_transactions: number;
  unique_tor_exit_nodes: number;
  tor_timing_entropy: number;
  average_tor_propagation_delay_sec: number;
  average_normal_propagation_delay_sec: number;
  top_tor_exit_countries: { country: string; tx_count: number }[];
  methodology: string;
}

export interface AlertScanStatus {
  state: 'idle' | 'running' | 'complete' | 'failed';
  phase: string;
  processed: number;
  total: number;
  elapsed_seconds: number;
}

export const api = {
  getAlertScanStatus: (signal?: AbortSignal) => fetchJson<AlertScanStatus>('/alerts/scan-status', { signal }),
  getHealth: () => fetchJson<HealthResponse>('/health'),
  getEntity: (address: string) => fetchJson<EntityResponse>(`/entity/${address}`),
  getEntityCluster: (address: string) => fetchJson<ClusterResponse>(`/entity/${address}/cluster`),
  getTransaction: (txid: number | string) => fetchJson<TransactionResponse>(`/transaction/${txid}`),
  getTransactionFlow: (txid: number | string) => fetchJson<any>(`/transaction/${txid}/flow`),
  getGraph: (scenarioId: string) => fetchJson<ScenarioGraph>(`/graph/${scenarioId}`),
  getGraphCommunities: (scenarioId: string) => fetchJson<any>(`/graph/${scenarioId}/communities`),
  getTrace: (source: string, target: string, maxDepth = 5) =>
    fetchJson<TraceResponse>(`/trace?src=${encodeURIComponent(source)}&dst=${encodeURIComponent(target)}&max_depth=${maxDepth}`),
  getTaint: (seedAddress: string, maxDepth = 4) =>
    fetchJson<TaintResponse>(`/taint?seed_address=${encodeURIComponent(seedAddress)}&max_depth=${maxDepth}`),
  getAlerts: (minConfidence = 0.5, limit = 50, patternType?: string) => {
    const params = new URLSearchParams({
      min_confidence: String(minConfidence),
      limit: String(limit),
    });
    if (patternType) {
      params.append('pattern_type', patternType);
    }
    return fetchJson<{ total_alerts: number; alerts: AlertSummary[] }>(`/alerts?${params.toString()}`);
  },
  getAlertEvidence: (candidateId: string) => fetchJson<EvidenceResponse>(`/alerts/${encodeURIComponent(candidateId)}/evidence`),
  getScenarios: (prefix?: string, page = 1, pageSize = 20) => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (prefix) {
      params.append('prefix', prefix);
    }
    return fetchJson<{
      total_scenarios: number;
      page: number;
      page_size: number;
      scenarios: Array<{
        scenario_id: string;
        transaction_count: number;
        total_volume_btc: number;
        primary_node_type: string;
      }>;
    }>(`/scenarios?${params.toString()}`);
  },
  getScenario: (scenarioId: string) => fetchJson<any>(`/scenarios/${scenarioId}`),
  getStatsOverview: () => fetchJson<any>('/stats/overview'),
  getStatsTelemetry: () => fetchJson<{
    total_transactions: number;
    total_unique_wallets: number;
    total_scenarios: number;
    node_type_distribution: Record<string, number>;
    top_asns: Record<string, number>;
    top_countries: Record<string, number>;
    script_type_distribution: Record<string, number>;
    average_propagation_latency_ms: Record<string, number>;
  }>('/stats/telemetry'),
  getBenchmark: () => fetchJson<{
    dataset_version: string;
    evaluation_scope: string;
    candidate_alerts_flagged: number;
    performance_metrics: {
      peeling_chain: { precision: number; recall: number; f1_score: number; detected_chains: number };
      layering: { precision: number; recall: number; f1_score: number; detected_structures: number };
      mixing_coinjoin: { precision: number; recall: number; f1_score: number; detected_rounds: number };
      ransomware: { precision: number; recall: number; f1_score: number; detected_campaigns: number };
    };
    overall_macro_f1: number;
    average_inference_latency_ms: number;
  }>('/eval/benchmark'),
  getAnomalyScore: (scenarioId: string) => fetchJson<{
    scenario_id: string;
    isolation_forest_score: number;
    anomaly_level: 'LOW' | 'MEDIUM' | 'HIGH';
    n_transactions: number;
    mean_propagation_delta_ms: number;
    suspicious_node_ratio: number;
    message: string;
  }>(`/anomaly/${encodeURIComponent(scenarioId)}`),
  search: (query: string) => fetchJson<{
    query: string;
    match_type: 'TRANSACTION' | 'WALLET' | 'SCENARIO' | 'TELEMETRY' | 'UNKNOWN';
    matches: any[];
  }>(`/search?q=${encodeURIComponent(query)}`),
  getDossier: (txid: number | string) => fetchJson<DossierResponse>(`/api/dossier/${txid}`),
  getTorSummary: () => fetchJson<TorSummary>('/api/intel/tor-summary'),
  getTorProfiler: (txid: number | string) => fetchJson<any>(`/api/intel/tor-profiler/${txid}`),
  getStreamBatch: (limit = 20, offset = 0, torOnly = false) =>
    fetchJson<any>(`/api/stream/batch?limit=${limit}&offset=${offset}&tor_only=${torOnly}`),
  ingestTransaction: (payload: any) =>
    fetchJson<any>('/api/ingest/transaction', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  ingestFile: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetchJson<any>('/api/ingest/file', {
      method: 'POST',
      body: formData,
    });
  },
  getIngestScenarioAnalysis: (scenarioId: string) =>
    fetchJson<IngestScenarioAnalysis>(`/api/ingest/scenario/${encodeURIComponent(scenarioId)}/analysis`),
  getIngestSample: (typology = 'ransomware') =>
    fetchJson<any>(`/api/ingest/sample?typology=${encodeURIComponent(typology)}`),
  getIngestSamplePair: () =>
    fetchJson<{ status: string; sample_count: number; ledger_csv: string; network_csv: string }>('/api/ingest/sample-pair'),
  listSavedDossiers: () => fetchJson<any[]>('/api/dossier/saved/list'),
  correlateFiles: (ledgerFile: File, networkFile: File) => {
    const formData = new FormData();
    formData.append('ledger_file', ledgerFile);
    formData.append('network_file', networkFile);
    return fetchJson<any>('/api/ingest/correlate', {
      method: 'POST',
      body: formData,
    });
  },
  listCases: () => fetchJson<any>('/cases'),
  getActiveCase: () => fetchJson<any>('/cases/active'),
  setActiveCase: (caseName: string) =>
    fetchJson<any>('/cases/active', {
      method: 'POST',
      body: JSON.stringify({ case_name: caseName }),
    }),
  initCase: (caseName: string) =>
    fetchJson<any>('/cases/init', {
      method: 'POST',
      body: JSON.stringify({ case_name: caseName }),
    }),
  getCaseLs: (caseName = 'active') =>
    fetchJson<any>(`/cases/${encodeURIComponent(caseName)}/ls`),
  saveCaseArtifact: (payload: { command_name: string; identifier: string; data: any; subfolder?: string; case_name?: string }) =>
    fetchJson<any>(`/cases/${encodeURIComponent(payload.case_name || 'active')}/save`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
};
