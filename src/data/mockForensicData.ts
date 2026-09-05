import { ForensicNode, ForensicLink, KernelLogEntry, CommandDescriptor } from '../types/terminal';

export const INITIAL_NODES: ForensicNode[] = [
  {
    id: '12dhqUGwzF6c6eW5F7DkyXyqBmW1',
    label: 'PRIMARY_SUSPECT_ORIGIN',
    type: 'SUSPECT',
    riskScore: 94,
    clusterId: 'entity_12dhqUGwzF6c',
    balanceBtc: 14.52,
    txCount: 38,
    firstSeen: '2014-03-15 09:22:41 UTC',
    lastSeen: '2014-03-15 14:45:00 UTC',
    tags: ['PEELING_CHAIN', 'BULLETPROOF_RELAY', 'HEIST_ORIGIN'],
    ownerAlias: 'HydraShadow / Ransomware-Subgroup-9',
    flags: ['SANCTIONED_AFFILIATION', 'HIGH_VELOCITY_PEEL', 'TOR_EXIT_ROUTING'],
    isLicitExchange: false
  },
  {
    id: '1EcgU6KKS36aF55d65f5aKKS9901',
    label: 'COINJOIN_MIXER_POOL',
    type: 'MIXER',
    riskScore: 88,
    clusterId: 'entity_1EcgU6KKS36a',
    balanceBtc: 8.52,
    txCount: 142,
    firstSeen: '2014-03-15 10:20:00 UTC',
    lastSeen: '2014-03-15 15:10:14 UTC',
    tags: ['COINJOIN_POOL', 'EQUAL_OUTPUT_SPLIT'],
    flags: ['MIXER_ROUTER', 'HIGH_ENTROPY_TIMING'],
    isLicitExchange: false
  },
  {
    id: '1PZDhrao899FF4A1B7766aa88220',
    label: 'INTERMEDIARY_PEEL_HOP',
    type: 'WALLET',
    riskScore: 76,
    clusterId: 'entity_1PZDhrao899F',
    balanceBtc: 3.20,
    txCount: 65,
    firstSeen: '2014-03-15 11:04:12 UTC',
    lastSeen: '2014-03-15 16:15:33 UTC',
    tags: ['PEEL_CHANGE', 'FAST_CONVERT'],
    flags: ['CHANGE_ADDRESS_REUSE'],
    isLicitExchange: false
  },
  {
    id: '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
    label: 'SATOSHI_GENESIS_RESERVE',
    type: 'WALLET',
    riskScore: 5,
    clusterId: 'entity_1A1zP1eP5QGe',
    balanceBtc: 50.0,
    txCount: 893,
    firstSeen: '2009-01-03 18:15:05 UTC',
    lastSeen: '2026-09-01 23:51:20 UTC',
    tags: ['GENESIS_BLOCK', 'HISTORICAL_WHITELIST'],
    flags: ['DORMANT_RESERVE'],
    isLicitExchange: false
  },
  {
    id: '1BinanceDepositHotWallet77889900',
    label: 'LICIT_EXCHANGE_HOTWALLET',
    type: 'EXCHANGE',
    riskScore: 12,
    clusterId: 'entity_binance_hot',
    balanceBtc: 540.22,
    txCount: 4120,
    firstSeen: '2017-06-12 18:30:11 UTC',
    lastSeen: '2026-09-01 19:40:02 UTC',
    tags: ['LICIT_EXCHANGE', 'KYC_VASP', 'GLOBAL_GATEWAY'],
    flags: ['WHITELISTED_VASP'],
    isLicitExchange: true
  },
  {
    id: '1VictimTreasuryColdVault001122',
    label: 'VICTIM_TREASURY_VAULT',
    type: 'WALLET',
    riskScore: 15,
    clusterId: 'entity_victim_org',
    balanceBtc: 55.10,
    txCount: 29,
    firstSeen: '2014-01-01 10:00:00 UTC',
    lastSeen: '2014-03-15 09:10:00 UTC',
    tags: ['TREASURY_VAULT', 'COMPROMISED_KEY'],
    flags: ['SOURCE_OF_DRAIN'],
    isLicitExchange: false
  }
];

export const INITIAL_LINKS: ForensicLink[] = [
  {
    source: '1VictimTreasuryColdVault001122',
    target: '12dhqUGwzF6c6eW5F7DkyXyqBmW1',
    txid: 58234917,
    amountBtc: 25.0,
    timestamp: '2014-03-15 09:22:41 UTC',
    isSuspicious: true,
    hopIndex: 1
  },
  {
    source: '12dhqUGwzF6c6eW5F7DkyXyqBmW1',
    target: '1PZDhrao899FF4A1B7766aa88220',
    txid: 58234918,
    amountBtc: 10.8,
    timestamp: '2014-03-15 10:14:02 UTC',
    isSuspicious: true,
    hopIndex: 2
  },
  {
    source: '1PZDhrao899FF4A1B7766aa88220',
    target: '1EcgU6KKS36aF55d65f5aKKS9901',
    txid: 58234919,
    amountBtc: 4.5,
    timestamp: '2014-03-15 11:05:18 UTC',
    isSuspicious: true,
    hopIndex: 3
  },
  {
    source: '1EcgU6KKS36aF55d65f5aKKS9901',
    target: '1BinanceDepositHotWallet77889900',
    txid: 58234920,
    amountBtc: 3.2,
    timestamp: '2014-03-15 12:40:55 UTC',
    isSuspicious: true,
    hopIndex: 4
  }
];

export const COMMAND_REGISTRY: CommandDescriptor[] = [
  {
    name: 'graph',
    aliases: ['g', 'dashboard', 'nodes'],
    usage: 'graph [scenario_id]',
    summary: 'Open interactive 3D WebGL / 2D link-analysis graph.',
    description: 'Renders full scenario transaction topology with wallets, transactions, and P2P IPs.',
    category: 'DISPLAY',
    examples: ['graph', 'graph peel_001', 'graph scenario_1042']
  },
  {
    name: 'inspect',
    aliases: ['i'],
    usage: 'inspect <txid | address>',
    summary: 'Audit UTXO inputs/outputs, fee metrics, and network origin telemetry.',
    description: 'Performs deep forensic inspection on any Bitcoin transaction hash or wallet address.',
    category: 'FORENSICS',
    examples: ['inspect 58234917', 'inspect 12dhqUGwzF6c6eW5F7DkyXyqBmW1']
  },
  {
    name: 'trace',
    aliases: ['route'],
    usage: 'trace <source_address> <target_address>',
    summary: 'Multi-hop BFS shortest path velocity tracer.',
    description: 'Calculates the fastest money laundering path between two wallets.',
    category: 'FORENSICS',
    examples: ['trace 1VictimTreasuryColdVault001122 1BinanceDepositHotWallet77889900']
  },
  {
    name: 'taint',
    aliases: [],
    usage: 'taint <seed_address>',
    summary: 'Forward dirty coin risk propagation (Haircut & FIFO models).',
    description: 'Tracks downstream tainted UTXOs with mathematical distance decay.',
    category: 'FORENSICS',
    examples: ['taint 12dhqUGwzF6c6eW5F7DkyXyqBmW1']
  },
  {
    name: 'alerts',
    aliases: ['alert'],
    usage: 'alerts',
    summary: 'View real-time detected typology candidates.',
    description: 'Fetches AI and heuristic alert queue for peeling chains, mixers, and layering.',
    category: 'FORENSICS',
    examples: ['alerts']
  },
  {
    name: 'dossier',
    aliases: ['report'],
    usage: 'dossier <txid>',
    summary: 'Generate court-admissible Section 91 Cr.P.C. Law Enforcement dossier.',
    description: 'Exports formal legal investigation report with VASP asset freeze directives.',
    category: 'FORENSICS',
    examples: ['dossier 58234917']
  },
  {
    name: 'tor',
    aliases: [],
    usage: 'tor [txid]',
    summary: 'Tor exit node timing entropy and de-anonymization profiler.',
    description: 'Computes Shannon timing entropy over gossip delays to unmask bot broadcasts.',
    category: 'SYSTEM',
    examples: ['tor', 'tor 58234917']
  },
  {
    name: 'status',
    aliases: ['sys', 'health'],
    usage: 'status',
    summary: 'Display in-memory engine telemetry and clustering statistics.',
    description: 'Reports total transactions loaded, unique wallets, and ML inference model status.',
    category: 'SYSTEM',
    examples: ['status']
  },
  {
    name: 'help',
    aliases: ['man', '?'],
    usage: 'help [command]',
    summary: 'Display interactive manual of all available terminal commands.',
    description: 'Comprehensive usage guide and parameter reference.',
    category: 'NAVIGATION',
    examples: ['help', 'help inspect', 'help trace']
  },
  {
    name: 'clear',
    aliases: ['cls'],
    usage: 'clear',
    summary: 'Clear the terminal output screen (Shortcut: Ctrl+L).',
    description: 'Clears previous command buffer.',
    category: 'NAVIGATION',
    examples: ['clear']
  }
];

export const INITIAL_LOGS: KernelLogEntry[] = [
  { id: '1', timestamp: '2026-09-05 13:50:00', uptime: '00:00:01', level: 'SYS', source: 'KERNEL', message: 'BitKaun Forensics Engine Initialized (WSL2/Linux 100% Offline).' },
  { id: '2', timestamp: '2026-09-05 13:50:02', uptime: '00:00:03', level: 'INFO', source: 'INGEST', message: 'Indexed 82,078 blockchain transactions & 284,401 wallets in memory.' },
  { id: '3', timestamp: '2026-09-05 13:50:04', uptime: '00:00:05', level: 'INFO', source: 'CLUSTERING', message: 'CIOH DSU Engine partitioned 244,363 entity clusters.' },
  { id: '4', timestamp: '2026-09-05 13:50:06', uptime: '00:00:07', level: 'WARN', source: 'TYPOLOGY', message: 'Detected 23,646 high-confidence typology candidates.' },
  { id: '5', timestamp: '2026-09-05 13:50:08', uptime: '00:00:09', level: 'CRIT', source: 'TOR_INTEL', message: 'High-risk Tor Exit Node burst detected on IP 38.148.127.142.' }
];
