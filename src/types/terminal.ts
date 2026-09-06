export type ViewMode = 'BANNER' | 'GRAPH' | 'INSPECT' | 'LOGS' | 'HELP' | 'TRACE' | 'SYS' | 'ALERTS' | 'TAINT' | 'DOSSIER' | 'TOR' | 'SCENARIOS';

export interface ForensicNode {
  id: string;
  label: string;
<<<<<<< HEAD
  type: 'WALLET' | 'MIXER' | 'EXCHANGE' | 'TRANSACTION' | 'SUSPECT' | 'IP';
  riskScore: number; // 0 - 100
  clusterId: string;
  balanceBtc: number;
  balanceEth?: number; // legacy alias fallback
=======
  type: 'WALLET' | 'MIXER' | 'EXCHANGE' | 'SMART_CONTRACT' | 'SUSPECT' | 'MERCHANT' | 'PEELING_CHAIN' | 'LAYERING_HUB';
  riskScore: number; // 0 - 100
  clusterId: string;
  balanceBtc?: number;
  balanceEth?: number; // Backward-compatibility alias
>>>>>>> origin/graph
  txCount: number;
  firstSeen: string;
  lastSeen: string;
  tags: string[];
  ownerAlias?: string;
  flags: string[];
<<<<<<< HEAD
  isLicitExchange?: boolean;
  address?: string;
  txid?: number;
=======
  candidateId?: string;
  candidateType?: string;
  asn?: string;
  relayIp?: string;
>>>>>>> origin/graph
  x?: number;
  y?: number;
  z?: number;
  vx?: number;
  vy?: number;
  vz?: number;
}

export interface ForensicLink {
  source: string;
  target: string;
<<<<<<< HEAD
  txid: number | string;
  txHash?: string; // legacy alias fallback
  amountBtc: number;
  amountEth?: number; // legacy alias fallback
=======
  txHash: string;
  amountBtc?: number;
  amountEth?: number; // Backward-compatibility alias
>>>>>>> origin/graph
  timestamp: string;
  isSuspicious: boolean;
  hopIndex?: number;
  candidateId?: string;
}

export interface KernelLogEntry {
  id: string;
  timestamp: string;
  uptime: string;
  level: 'INFO' | 'WARN' | 'CRIT' | 'SYS' | 'IPC';
  source: string;
  message: string;
  meta?: Record<string, any>;
}

export interface TerminalHistoryItem {
  id: string;
  type: 'INPUT' | 'OUTPUT' | 'SUCCESS' | 'ERROR' | 'INFO' | 'WARNING' | 'SYS';
  text: string;
  timestamp: string;
  clickableCmd?: string;
}

export interface CommandDescriptor {
  name: string;
  aliases: string[];
  usage: string;
  summary: string;
  description: string;
  category: 'NAVIGATION' | 'FORENSICS' | 'SYSTEM' | 'DISPLAY';
  examples: string[];
  options?: { flag: string; desc: string }[];
}
