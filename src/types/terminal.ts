export type ViewMode = 'BANNER' | 'GRAPH' | 'INSPECT' | 'LOGS' | 'HELP' | 'TRACE' | 'SYS';

export interface ForensicNode {
  id: string;
  label: string;
  type: 'WALLET' | 'MIXER' | 'EXCHANGE' | 'SMART_CONTRACT' | 'SUSPECT' | 'MERCHANT';
  riskScore: number; // 0 - 100
  clusterId: string;
  balanceEth: number;
  txCount: number;
  firstSeen: string;
  lastSeen: string;
  tags: string[];
  ownerAlias?: string;
  flags: string[];
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
  txHash: string;
  amountEth: number;
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
