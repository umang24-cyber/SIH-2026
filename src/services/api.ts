/**
 * Centralized Typed API Client for BitKaun Forensic Backend (FastAPI).
 * 100% Offline / Air-Gapped compliant.
 */

const BASE_URL = '';

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = endpoint.startsWith('/') ? `${BASE_URL}${endpoint}` : `${BASE_URL}/${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
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
  version: string;
  dataset: {
    loaded_transactions: number;
    unique_wallets: number;
    unique_scenarios: number;
    uptime_seconds: number;
  };
  clustering: {
    is_clustered: boolean;
    total_clusters: number;
  };
  typologies: {
    is_scanned: boolean;
    total_alerts: number;
  };
  ml_model: {
    is_loaded: boolean;
    model_type: string;
  };
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
    investigating_authority: string;
    statutory_mandates: string[];
  };
  transaction_evidence: {
    txid: number;
    block_timestamp: string;
    btc_value: number;
    input_addresses: string[];
    output_addresses: string[];
  };
  network_telemetry_attribution: {
    ip_address: string;
    isp: string;
    asn: string;
    country: string;
    is_tor_exit_node: boolean;
    propagation_delta_t_seconds: number;
  };
  entity_clustering: {
    entity_cluster_id: string;
    total_unmasked_wallets_in_cluster: number;
    sample_co_owned_addresses: string[];
  };
  threat_assessment: {
    composite_risk_score: number;
    risk_rating: string;
    detected_typologies: string[];
    taint_hop_flows_count: number;
  };
  statutory_legal_directives: string[];
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

export const api = {
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
  getAlerts: (minConfidence = 0.5, limit = 50) =>
    fetchJson<{ total_alerts: number; alerts: AlertSummary[] }>(`/alerts?min_confidence=${minConfidence}&limit=${limit}`),
  getAlertEvidence: (candidateId: string) => fetchJson<any>(`/alerts/${candidateId}/evidence`),
  getScenarios: (limit = 50, offset = 0) => fetchJson<any>(`/scenarios?limit=${limit}&offset=${offset}`),
  getScenario: (scenarioId: string) => fetchJson<any>(`/scenarios/${scenarioId}`),
  getStatsOverview: () => fetchJson<any>('/stats/overview'),
  getStatsTelemetry: () => fetchJson<any>('/stats/telemetry'),
  search: (query: string) => fetchJson<any>(`/search?query=${encodeURIComponent(query)}`),
  getDossier: (txid: number | string) => fetchJson<DossierResponse>(`/api/dossier/${txid}`),
  getTorSummary: () => fetchJson<TorSummary>('/api/intel/tor-summary'),
  getTorProfiler: (txid: number | string) => fetchJson<any>(`/api/intel/tor-profiler/${txid}`),
  getStreamBatch: (limit = 20, offset = 0, torOnly = false) =>
    fetchJson<any>(`/api/stream/batch?limit=${limit}&offset=${offset}&tor_only=${torOnly}`),
};
