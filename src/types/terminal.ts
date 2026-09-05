export type ViewMode = 'BANNER' | 'GRAPH' | 'INSPECT' | 'LOGS' | 'HELP' | 'TRACE' | 'SYS' | 'ALERTS' | 'TAINT' | 'DOSSIER' | 'TOR' | 'SCENARIOS';

export interface ForensicNode {
  id: string;
  label: string;
  type: 'WALLET' | 'MIXER' | 'EXCHANGE' | 'TRANSACTION' | 'SUSPECT' | 'IP';
  riskScore: number; // 0 - 100
  clusterId: string;
  balanceBtc: number;
  balanceEth?: number; // legacy alias fallback
  txCount: number;
  firstSeen: string;
  lastSeen: string;
  tags: string[];
  ownerAlias?: string;
  flags: string[];
  isLicitExchange?: boolean;
  address?: string;
  txid?: number;
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
  txid: number | string;
  txHash?: string; // legacy alias fallback
  amountBtc: number;
  amountEth?: number; // legacy alias fallback
  timestamp: string;
  isSuspicious: boolean;
  hopIndex?: number;
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
