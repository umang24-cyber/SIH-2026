import type {
  GraphData,
  GraphNode,
  GraphEdge,
  WalletNode,
  TransactionNode,
  IPNode,
} from "../types/graph";

import type {
  GraphNode as ScenarioNode,
  GraphEdge as ScenarioEdge,
} from "../data/forensicScenarios";

function getScenarioClusterId(
  node: ScenarioNode
): string {
  const label = node.label.toLowerCase();

  if (
    label.includes("origin") ||
    label.includes("peel") ||
    label.includes("change") ||
    node.type === "Transaction"
  ) {
    return "PEEL_CHAIN_ALPHA";
  }

  if (
    label.includes("bulletproof") ||
    String(
      node.properties.node_type ?? ""
    ).toLowerCase().includes("bulletproof")
  ) {
    return "SUSPICIOUS_INFRASTRUCTURE";
  }

  return "NETWORK_TELEMETRY";
}

export function adaptScenarioNode(
  node: ScenarioNode
): GraphNode {
  switch (node.type) {
   case "Wallet":
  return {
    id: node.id,
    type: "WALLET",
    label: node.label,
    x: node.x,
    y: node.y,
    address: node.properties.address ?? node.label,
    mlAnalysisStatus: "UNAVAILABLE",
    mlAnalysisMessage: "No backend scenario-level ML result is attached to this static demonstration graph.",
    transactionCount: undefined,
    clusterId: getScenarioClusterId(node),
    tags: [],
    firstSeen: undefined,
    lastSeen: undefined,
  };

   case "Transaction":
  return {
    id: node.id,
    type: "TRANSACTION",
    label: node.label,
    x: node.x,
    y: node.y,
    txid: String(node.properties.txid ?? node.id),
    amountBtc: undefined,
    feeBtc: node.properties.fee_btc,
    timestamp: node.properties.timestamp,
    inputCount: undefined,
    outputCount: undefined,
    confidenceScore: undefined,
    mlAnalysisStatus: "UNAVAILABLE",
    mlAnalysisMessage: "No backend scenario-level ML result is attached to this static demonstration graph.",
    clusterId: getScenarioClusterId(node),

    patternTags: [],
  };

    case "IP":
  return {
    id: node.id,
    type: "IP",
    label: node.label,
    x: node.x,
    y: node.y,
    ipAddress: node.properties.relay_ip ?? node.label,
    asn: node.properties.asn,
    country: node.properties.country_code,
    isp: node.properties.isp,
    latency: node.properties.propagation_delta_ms,
    infrastructureType: node.properties.node_type,
    mlAnalysisStatus: "UNAVAILABLE",
    mlAnalysisMessage: "No backend scenario-level ML result is attached to this static demonstration graph.",
    clusterId: getScenarioClusterId(node),

  };
  }
}

export function adaptScenarioEdge(
  edge: ScenarioEdge
): GraphEdge {
  return {
    id: edge.id,
    source: edge.source,
    target: edge.target,
    type: edge.type,
    amountBtc: edge.amount_btc,
  };
}


export function adaptScenarioToGraphData(
  nodes: ScenarioNode[],
  edges: ScenarioEdge[]
): GraphData {
  return {
    nodes: nodes.map(adaptScenarioNode),
    edges: edges.map(adaptScenarioEdge),
  };
}
