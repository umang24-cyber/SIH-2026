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
    name: 'search',
    aliases: ['find', 'query'],
    usage: 'search <query>',
    summary: 'Universal search across TxID, wallet address, IP, ASN, or scenario cluster.',
    description: 'Searches all indexed transactions, entities, scenario clusters, and network relay infrastructure.',
    category: 'FORENSICS',
    examples: ['search 881920041', 'search 1PeelHeadWallet0001', 'search AS49981', 'search peeling_chain_04651']
  },
  {
    name: 'scenarios',
    aliases: ['clusters'],
    usage: 'scenarios [prefix] [page]',
    summary: 'Paginated scenario cluster explorer with transaction counts and financial volume.',
    description: 'Browse scenario clusters partitioned by laundering typology (peeling, mixing, layering, ransomware, licit).',
    category: 'FORENSICS',
    examples: ['scenarios', 'scenarios peel 1', 'scenarios mix 1', 'scenarios ransom 1']
  },
  {
    name: 'benchmark',
    aliases: ['eval', 'metrics', 'accuracy'],
    usage: 'benchmark',
    summary: 'V8 model evaluation scorecard (Precision, Recall, F1, and Latency).',
    description: 'Quantitative accuracy benchmark across peeling chains, layering hubs, mixing rounds, and ransomware campaigns.',
    category: 'SYSTEM',
    examples: ['benchmark', 'eval']
  },
  {
    name: 'telemetry',
    aliases: ['stats', 'p2p'],
    usage: 'telemetry',
    summary: 'Global network telemetry, propagation latency Δt, and relay distributions.',
    description: 'Aggregates P2P origin node infrastructure (Tor, VPN, Datacenter, Residential), top ASNs, and countries.',
    category: 'SYSTEM',
    examples: ['telemetry', 'stats']
  },
  {
    name: 'communities',
    aliases: ['community', 'syndicates'],
    usage: 'communities [scenario_id]',
    summary: 'NetworkX greedy modularity partition showing co-acting entity syndicates.',
    description: 'Discovers dense co-acting wallet and transaction clusters within a scenario subgraph.',
    category: 'FORENSICS',
    examples: ['communities peeling_chain_04651', 'communities live_ransomware_probe']
  },
  {
    name: 'flow',
    aliases: ['decompose'],
    usage: 'flow <txid>',
    summary: 'Financial UTXO input-to-output decomposition and CIOH entity clusters.',
    description: 'Decomposes transaction inputs, entity cluster roots, miner fees, and broadcast network telemetry.',
    category: 'FORENSICS',
    examples: ['flow 881920041', 'flow 322596997']
  },
  {
    name: 'anomaly',
    aliases: ['unusual'],
    usage: 'anomaly [scenario_id]',
    summary: 'Isolation Forest anomaly & unusualness score (0-100).',
    description: 'Evaluates structural and temporal deviation against normal licit Bitcoin reference distribution (SIH PS146).',
    category: 'FORENSICS',
    examples: ['anomaly peeling_chain_04651', 'anomaly live_ransomware_probe']
  },
  {
    name: 'correlate',
    aliases: ['upload', 'dualstream'],
    usage: 'correlate',
    summary: 'Dual-stream Ledger & P2P Telemetry correlation and V8 ML scoring view.',
    description: 'Upload and merge on-chain UTXO transaction arrays with pre-block P2P network telemetry with instant SHAP attribution.',
    category: 'FORENSICS',
    examples: ['correlate', 'upload']
  },
  {
    name: 'ingest',
    aliases: ['inject'],
    usage: 'ingest sample [type] | ingest <raw_json>',
    summary: 'Dynamic live transaction injection with real-time ML risk scoring.',
    description: 'Inject custom raw transaction JSON or benchmark samples (ransomware, peeling, mixing, licit) into in-memory engine.',
    category: 'SYSTEM',
    examples: ['ingest sample ransomware', 'ingest sample peeling', 'ingest sample mixing']
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
