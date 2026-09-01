import { ForensicNode, ForensicLink, KernelLogEntry, CommandDescriptor } from '../types/terminal';

export const INITIAL_NODES: ForensicNode[] = [
  {
    id: '0x71C84A9E',
    label: 'PRIMARY_SUSPECT_01',
    type: 'SUSPECT',
    riskScore: 94,
    clusterId: 'CLUSTER_ALPHA_HEIST',
    balanceEth: 1420.45,
    txCount: 384,
    firstSeen: '2026-08-14 03:12:09 UTC',
    lastSeen: '2026-09-01 22:45:00 UTC',
    tags: ['EXPLOITER', 'PEELING_CHAIN', 'DIRECT_HEIST_INFLOW'],
    ownerAlias: 'HydraShadow / Lazarus-Subgroup-9',
    flags: ['SANCTIONED_AFFILIATION', 'HIGH_VELOCITY_DISBURSEMENT', 'MIXER_ROUTING']
  },
  {
    id: '0x44B12D03',
    label: 'MIXER_HOP_POOL_01',
    type: 'MIXER',
    riskScore: 88,
    clusterId: 'CLUSTER_ALPHA_HEIST',
    balanceEth: 852.10,
    txCount: 1420,
    firstSeen: '2026-08-15 11:20:00 UTC',
    lastSeen: '2026-09-01 23:10:14 UTC',
    tags: ['TORNADO_RELAY', 'SMART_CONTRACT', 'SPLIT_TRANCHE'],
    flags: ['TORNADO_CASH_ROUTER', 'HIGH_ENTROPY_TIMING']
  },
  {
    id: '0x99FF4A1B',
    label: 'INTERMEDIARY_HUB_09',
    type: 'WALLET',
    riskScore: 76,
    clusterId: 'CLUSTER_ALPHA_HEIST',
    balanceEth: 320.00,
    txCount: 65,
    firstSeen: '2026-08-20 08:04:12 UTC',
    lastSeen: '2026-09-01 20:15:33 UTC',
    tags: ['AGGREGATOR', 'FAST_CONVERT'],
    flags: ['MULTISIG_THRESHOLD_ALTERED', 'SUSPICIOUS_GAS_PRICE']
  },
  {
    id: '0x1A2B3C4D',
    label: 'BRIDGE_CONTRACT_L2',
    type: 'SMART_CONTRACT',
    riskScore: 42,
    clusterId: 'CLUSTER_BRIDGE_OPS',
    balanceEth: 14920.80,
    txCount: 89304,
    firstSeen: '2025-01-10 00:00:00 UTC',
    lastSeen: '2026-09-01 23:51:20 UTC',
    tags: ['ZK_BRIDGE', 'CROSS_CHAIN_ESCROW'],
    flags: ['HIGH_VOLUME_TRANSIT']
  },
  {
    id: '0xEE3388A1',
    label: 'UNLICENSED_OTC_DESK',
    type: 'EXCHANGE',
    riskScore: 82,
    clusterId: 'CLUSTER_CASHOUT_RING',
    balanceEth: 540.22,
    txCount: 412,
    firstSeen: '2026-06-12 18:30:11 UTC',
    lastSeen: '2026-09-01 19:40:02 UTC',
    tags: ['NO_KYC_OTC', 'P2P_RAMP', 'SE ASIA_CORRIDOR'],
    flags: ['UNREGISTERED_MSB', 'RAPID_FIAT_EXIT']
  },
  {
    id: '0x5C8821FF',
    label: 'VICTIM_TREASURY_VAULT',
    type: 'WALLET',
    riskScore: 12,
    clusterId: 'VICTIM_ORG_REVENUE',
    balanceEth: 55.10,
    txCount: 2901,
    firstSeen: '2024-11-01 10:00:00 UTC',
    lastSeen: '2026-08-14 03:10:00 UTC',
    tags: ['DEFI_VAULT', 'COMPROMISED_KEY'],
    flags: ['SOURCE_OF_DRAIN']
  },
  {
    id: '0xBB001122',
    label: 'SYNTHETIC_LIQUIDITY_POOL',
    type: 'SMART_CONTRACT',
    riskScore: 35,
    clusterId: 'DEFI_CORE_PROTOCOL',
    balanceEth: 28400.00,
    txCount: 240911,
    firstSeen: '2025-03-01 00:00:00 UTC',
    lastSeen: '2026-09-01 23:50:00 UTC',
    tags: ['AMM_V3', 'FLASHLOAN_SOURCE'],
    flags: ['FLASHLOAN_FACILITY_UTILIZED']
  },
  {
    id: '0x77DD9900',
    label: 'DARKNET_ESCROW_NODE',
    type: 'SUSPECT',
    riskScore: 98,
    clusterId: 'CLUSTER_CASHOUT_RING',
    balanceEth: 980.50,
    txCount: 914,
    firstSeen: '2026-04-05 09:22:15 UTC',
    lastSeen: '2026-09-01 21:05:44 UTC',
    tags: ['BLACK_MARKET', 'TOR_HIDDEN_SERVICE', 'RANSOMWARE_AFFILIATE'],
    flags: ['DIRECT_RANSOM_COLLECTOR', 'HIGH_SEVERITY_INTERCEPT']
  }
];

export const INITIAL_LINKS: ForensicLink[] = [
  {
    source: '0x5C8821FF',
    target: '0x71C84A9E',
    txHash: '0x9a8f3b20c1d4e7f8a5b2c9d1e3f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0',
    amountEth: 2500.0,
    timestamp: '2026-08-14 03:12:09 UTC',
    isSuspicious: true,
    hopIndex: 1
  },
  {
    source: '0x71C84A9E',
    target: '0x44B12D03',
    txHash: '0x1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c',
    amountEth: 1080.0,
    timestamp: '2026-08-15 11:20:00 UTC',
    isSuspicious: true,
    hopIndex: 2
  },
  {
    source: '0x44B12D03',
    target: '0x99FF4A1B',
    txHash: '0x3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d',
    amountEth: 450.0,
    timestamp: '2026-08-20 08:04:12 UTC',
    isSuspicious: true,
    hopIndex: 3
  },
  {
    source: '0x99FF4A1B',
    target: '0xEE3388A1',
    txHash: '0x5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f',
    amountEth: 320.0,
    timestamp: '2026-08-25 14:18:22 UTC',
    isSuspicious: true,
    hopIndex: 4
  },
  {
    source: '0x71C84A9E',
    target: '0x1A2B3C4D',
    txHash: '0x7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b',
    amountEth: 600.0,
    timestamp: '2026-08-16 19:44:01 UTC',
    isSuspicious: true,
    hopIndex: 2
  },
  {
    source: '0x1A2B3C4D',
    target: '0x77DD9900',
    txHash: '0x8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c',
    amountEth: 580.0,
    timestamp: '2026-08-18 21:00:30 UTC',
    isSuspicious: true,
    hopIndex: 3
  },
  {
    source: '0xBB001122',
    target: '0x71C84A9E',
    txHash: '0x9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d',
    amountEth: 12000.0,
    timestamp: '2026-08-14 03:11:50 UTC',
    isSuspicious: false,
    hopIndex: 0
  }
];

export const INITIAL_LOGS: KernelLogEntry[] = [
  {
    id: 'log-001',
    timestamp: '23:58:01.104',
    uptime: '[   0.000000]',
    level: 'SYS',
    source: 'kernel:holmes-core',
    message: 'Linux version 6.9.4-forensic-holmes (root@sih-forensics) (gcc 13.2.0) #1 SMP PREEMPT_DYNAMIC'
  },
  {
    id: 'log-002',
    timestamp: '23:58:01.142',
    uptime: '[   0.041012]',
    level: 'INFO',
    source: 'kernel:pci_bus',
    message: 'Forensic memory bus registered: 0x00000000-0x3FFFFFFF (1024MB isolated TTY workspace)'
  },
  {
    id: 'log-003',
    timestamp: '23:58:01.200',
    uptime: '[   0.098421]',
    level: 'INFO',
    source: 'graph:webgl_engine',
    message: '3D Force-Directed WebGL acceleration pipeline mounted. Hardware shader cores: 16'
  },
  {
    id: 'log-004',
    timestamp: '23:58:02.410',
    uptime: '[   1.309482]',
    level: 'WARN',
    source: 'mempool:eth_watch',
    message: 'Peeling chain detected: Source wallet 0x71C84A9E executed 4 split disbursements within 180s'
  },
  {
    id: 'log-005',
    timestamp: '23:58:04.912',
    uptime: '[   3.811094]',
    level: 'CRIT',
    source: 'aml:sanction_interceptor',
    message: 'CRITICAL ALERT: Target 0x77DD9900 matched OFAC SDN / Darknet Escrow blacklist footprint!'
  },
  {
    id: 'log-006',
    timestamp: '23:58:08.120',
    uptime: '[   7.020119]',
    level: 'IPC',
    source: 'holmes:dossier_sync',
    message: 'IPC message delivered to /dev/shm/investigation_dossier.lock [8 nodes, 7 links indexed]'
  },
  {
    id: 'log-007',
    timestamp: '23:58:12.784',
    uptime: '[  11.684022]',
    level: 'INFO',
    source: 'sec:audit_daemon',
    message: 'Forensic session integrity: SHA256[e4b8a21f...7c90] VERIFIED. Key isolation intact.'
  }
];

export const COMMAND_REGISTRY: CommandDescriptor[] = [
  {
    name: 'help',
    aliases: ['man', '?', 'info'],
    usage: 'help [command]',
    summary: 'Display interactive Linux-style forensic manual and command syntax.',
    description: 'Displays the complete forensic command reference, parameter specifications, alias dictionary, and step-by-step investigation procedures.',
    category: 'NAVIGATION',
    examples: ['help', 'man inspect', 'help trace']
  },
  {
    name: 'graph',
    aliases: ['nodes', 'g', 'ls nodes'],
    usage: 'graph [filter]',
    summary: 'Mount and maximize the full-viewport 3D Force-Directed Graph canvas.',
    description: 'Switches the primary TTY stage to the WebGL 3D Graph. Renders nodes as wireframe phosphor cubes, calculates physical spatial repulsive forces, and pulses directional photon beams along transaction links. Left click drag rotates, right click pans, scroll zooms, and clicking any node automatically opens its inspector dossier.',
    category: 'NAVIGATION',
    examples: ['graph', 'nodes', 'g']
  },
  {
    name: 'inspect',
    aliases: ['cat', 'hex', 'view'],
    usage: 'inspect <NODE_ID>',
    summary: 'Mount forensic byte hexdump and entity intelligence dossier.',
    description: 'Renders raw memory byte hexdump, AML risk classification scores, linked cluster affiliations, transaction frequency, and cryptographic addresses for a specified entity ID.',
    category: 'FORENSICS',
    examples: ['inspect 0x71C84A9E', 'cat 0x77DD9900', 'inspect 0x44B12D03']
  },
  {
    name: 'trace',
    aliases: ['tr', 'path', 'flow'],
    usage: 'trace <SRC_ID> <DST_ID>',
    summary: 'Calculate and visually highlight the multi-hop fund flow in 3D space.',
    description: 'Computes the shortest and highest-velocity transaction path between two addresses, detailing each intermediary hop, transferred ETH volume, timestamps, and laundering markers.',
    category: 'FORENSICS',
    examples: [
      'trace 0x5C8821FF 0xEE3388A1',
      'trace 0x71C84A9E 0x99FF4A1B',
      'tr 0x71C84A9E 0x77DD9900'
    ]
  },
  {
    name: 'dmesg',
    aliases: ['logs', 'd', 'tail -f'],
    usage: 'dmesg [filter]',
    summary: 'Stream live rolling kernel logs, AML intercepts, and system events.',
    description: 'Displays real-time system audit logs, memory pool intercepts, and automated threat intelligence detection alerts.',
    category: 'SYSTEM',
    examples: ['dmesg', 'logs', 'd']
  },
  {
    name: 'home',
    aliases: ['banner', 'cd ~', 'cd', 'landing'],
    usage: 'home',
    summary: 'Return to the root landing screen with the detective ASCII art.',
    description: 'Restores the root TTY1 welcome artwork (Evidence Scanner, Noir Fedora, Filigree Pipe), active investigation status, and quick-start tips.',
    category: 'NAVIGATION',
    examples: ['home', 'cd ~', 'banner']
  },
  {
    name: 'sound',
    aliases: ['audio', 'mute'],
    usage: 'sound <on|off|toggle>',
    summary: 'Toggle procedural retro terminal keyboard clicks and beep synthesis.',
    description: 'Enables or disables the procedural Web Audio synthesizer that generates mechanical VT100 keystrokes and kernel alert chirps.',
    category: 'SYSTEM',
    examples: ['sound on', 'sound off', 'sound']
  },
  {
    name: 'status',
    aliases: ['sys', 'top', 'whoami', 'uname'],
    usage: 'status',
    summary: 'Display forensic kernel system diagnostics, memory, and session state.',
    description: 'Outputs system uptime, active investigator PID, mapped cluster counts, and memory buffer allocations.',
    category: 'SYSTEM',
    examples: ['status', 'top', 'whoami']
  },
  {
    name: 'clear',
    aliases: ['cls'],
    usage: 'clear',
    summary: 'Flush current terminal stdout history buffer (Shortcut: Ctrl+L).',
    description: 'Clears the bottom terminal command output history buffer and positions the cursor at the top.',
    category: 'NAVIGATION',
    examples: ['clear', 'cls']
  }
];

export const MOCK_HEX_DUMPS: Record<string, string[]> = {
  '0x71C84A9E': [
    '00000000  7f 45 4c 46 02 01 01 00  00 00 00 00 00 00 00 00  |.ELF............|',
    '00000010  03 00 3e 00 01 00 00 00  a0 14 00 00 00 00 00 00  |..>.............|',
    '00000020  40 00 00 00 00 00 00 00  78 3b 00 00 00 00 00 00  |@.......x;......|',
    '00000030  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|',
    '00000040  06 00 00 00 04 00 00 00  40 00 00 00 00 00 00 00  |........@.......|',
    '00000050  a8 02 00 00 00 00 00 00  71 c8 4a 9e f4 1b aa 90  |........q.J.....|',
    '00000060  a9 05 38 ff e1 09 a2 40  10 80 00 00 00 00 00 00  |..8....@........|',
    '00000070  ff ff ff ff 00 00 00 00  c0 de 48 65 69 73 74 21  |..........Heist!|'
  ],
  '0x77DD9900': [
    '00000000  44 41 52 4b 4e 45 54 5f  45 53 43 52 4f 57 5f 56  |DARKNET_ESCROW_V|',
    '00000010  32 2e 34 2e 31 00 00 00  77 dd 99 00 aa ff 00 11  |2.4.1...w.......|',
    '00000020  00 00 03 d4 00 00 00 00  20 26 04 05 09 22 15 00  |.... ......"....|',
    '00000030  74 6f 72 3a 2f 2f 64 61  72 6b 6d 61 72 6b 65 74  |tor://darkmarket|',
    '00000040  2e 6f 6e 69 6f 6e 2f 62  61 6c 61 6e 63 65 2f 78  |.onion/balance/x|',
    '00000050  80 00 00 00 de ad be ef  ca fe ba be 00 00 00 00  |................|'
  ]
};
