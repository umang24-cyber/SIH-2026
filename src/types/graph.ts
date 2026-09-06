export type NodeType = "WALLET" | "TRANSACTION" | "IP";

export interface BaseNode {
  id: string;
  type: NodeType;
  label: string;
  x?: number;
  y?: number;
  riskScore?: number;
  mlAnalysisStatus?: "AVAILABLE" | "UNAVAILABLE";
  mlAnalysisMessage?: string;
  scoreScope?: "SCENARIO";
  isIllicit?: boolean;
  binaryConfidence?: number;
  typologyConfidence?: number;
  predictedTypology?: string;
  anomalyScore?: number;
  anomalyLabel?: string;
}

export interface WalletNode extends BaseNode {
  type: "WALLET";
  address: string;
  transactionCount?: number;
  clusterId?: string;
  tags?: string[];
  firstSeen?: string;
  lastSeen?: string;
}

export interface TransactionNode extends BaseNode {
  type: "TRANSACTION";
  txid: string;
  amountBtc?: number;
  feeBtc?: number;
  timestamp?: string;
  inputCount?: number;
  outputCount?: number;
  confidenceScore?: number;
  patternTags?: string[];
  clusterId?: string;
}

export interface IPNode extends BaseNode {
  type: "IP";
  ipAddress: string;
  asn?: string;
  country?: string;
  isp?: string;
  latency?: number;
  infrastructureType?: string;
  clusterId?: string;
}

export type GraphNode =
  | WalletNode
  | TransactionNode
  | IPNode;

export type EdgeType =
  | "SENT"
  | "RECEIVED"
  | "BROADCAST";

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  amountBtc?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export type GraphMode =
  | "OVERVIEW"
  | "FLOW"
  | "RISK"
  | "CLUSTER"
  | "NETWORK"
  | "PEEL"
  | "LAYER";

export const DEFAULT_GRAPH_MODE: GraphMode = "OVERVIEW";
