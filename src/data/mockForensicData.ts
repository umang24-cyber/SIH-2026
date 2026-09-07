import { ForensicNode, ForensicLink, KernelLogEntry, CommandDescriptor } from '../types/terminal';

// Real command registry with live dataset examples
export const COMMAND_REGISTRY: CommandDescriptor[] = [
  {
    name: 'graph',
    aliases: ['dashboard', 'g', 'nodes'],
    usage: 'graph [scenario_id]',
    summary: 'Open interactive 3D WebGL on-chain transaction graph with Bitcoin medallion sprites.',
    description: 'Renders 3D force-directed WebGL topology with Bitcoin sprites, dynamic trust colors, and moving transaction orbs.',
    category: 'DISPLAY',
    examples: ['graph', 'graph licit_00001', 'graph ransom_0001', 'graph peeling_0001']
  },
  {
    name: 'inspect',
    aliases: ['i'],
    usage: 'inspect <txid | address>',
    summary: 'Audit UTXO inputs/outputs, fee metrics, and network origin telemetry.',
    description: 'Performs deep forensic inspection on any Bitcoin transaction hash or wallet address.',
    category: 'FORENSICS',
    examples: ['inspect 322596997', 'inspect 18hvz1KnqUjLRr3KHifSbMDi6m']
  },
  {
    name: 'trace',
    aliases: ['route'],
    usage: 'trace <source_address> <target_address>',
    summary: 'Multi-hop BFS shortest path velocity tracer.',
    description: 'Calculates the fastest money laundering path between two wallets.',
    category: 'FORENSICS',
    examples: ['trace 18hvz1KnqUjLRr3KHifSbMDi6m 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa']
  },
  {
    name: 'taint',
    aliases: [],
    usage: 'taint <seed_address>',
    summary: 'Forward dirty coin risk propagation (Haircut & FIFO models).',
    description: 'Tracks downstream tainted UTXOs with mathematical distance decay.',
    category: 'FORENSICS',
    examples: ['taint 18hvz1KnqUjLRr3KHifSbMDi6m']
  },
  {
    name: 'alerts',
    aliases: ['alert'],
    usage: 'alerts [--detail <candidate_id>] [--limit <n>]',
    summary: 'Prioritized AML forensic alerts feed ranked by ML risk score and SHAP evidence.',
    description: 'Queries live /alerts and /alerts/{id}/evidence endpoints. Displays prioritized queue of laundering typologies and deep explainable AI dossiers.',
    category: 'FORENSICS',
    examples: ['alerts', 'alerts --limit 10', 'alerts --detail cand_ransom_ransomware_03287_187888339']
  },
  {
    name: 'dossier',
    aliases: ['report'],
    usage: 'dossier <txid>',
    summary: 'Generate a system-generated investigative summary for authorized review.',
    description: 'Exports a synthetic demonstration report with review-oriented recommendations.',
    category: 'FORENSICS',
    examples: ['dossier 322596997']
  },
  {
    name: 'tor',
    aliases: [],
    usage: 'tor [txid]',
    summary: 'Tor exit node timing entropy and de-anonymization profiler.',
    description: 'Computes Shannon timing entropy over gossip delays to unmask bot broadcasts.',
    category: 'SYSTEM',
    examples: ['tor', 'tor 322596997']
  },
  {
    name: 'logs',
    aliases: ['log', 'stream'],
    usage: 'logs',
    summary: 'Stream live mempool gossip frames and block ingestion events.',
    description: 'Queries live streaming correlator buffer for incoming P2P transactions.',
    category: 'SYSTEM',
    examples: ['logs']
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

// Fallback empty type-safe arrays (Zero mock placeholders)
export const INITIAL_NODES: ForensicNode[] = [];
export const INITIAL_LINKS: ForensicLink[] = [];
export const INITIAL_LOGS: KernelLogEntry[] = [];
