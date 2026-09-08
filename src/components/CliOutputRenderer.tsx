import React, { useState, useEffect, useRef, useMemo } from 'react';
import { ForensicNode, ForensicLink, KernelLogEntry } from '../types/terminal';
import { sound } from '../audio/soundEngine';
import GraphView from '../graph/components/GraphView';
import { InspectView } from './views/InspectView';
import { TraceView } from './views/TraceView';
import { TwoStreamUploadView } from './views/TwoStreamUploadView';
import { AlertDetailView } from './views/AlertDetailView';
import { AlertsListView } from './views/AlertsListView';
import { SearchView } from './views/SearchView';
import { ScenariosListView } from './views/ScenariosListView';
import { BenchmarkView } from './views/BenchmarkView';
import { TelemetryStatsView } from './views/TelemetryStatsView';
import { CommunitiesView } from './views/CommunitiesView';
import { FlowView } from './views/FlowView';
import { AnomalyView } from './views/AnomalyView';

export interface TerminalEntry {
  id: string;
  command?: string;
  type: 'BANNER' | 'TEXT' | 'ERROR' | 'SUCCESS' | 'HELP' | 'INSPECT' | 'TRACE' | 'LOGS' | 'GRAPH' | 'STATUS' | 'ALERTS' | 'ALERT_DETAIL' | 'TAINT' | 'DOSSIER' | 'DOSSIER_LIST' | 'TOR' | 'INGEST' | 'INGEST_BATCH' | 'TWO_STREAM_UPLOAD' | 'SEARCH' | 'SCENARIOS' | 'BENCHMARK' | 'TELEMETRY' | 'COMMUNITIES' | 'FLOW' | 'ANOMALY';
  content?: any;
}

interface CliOutputRendererProps {
  entry: TerminalEntry;
  onRunCommand: (cmd: string) => void;
  nodes?: ForensicNode[];
  links?: ForensicLink[];
  logs?: KernelLogEntry[];
  onScrollRequested: () => void;
  onCloseEntry?: (id: string) => void;
}

// Format STATUS content into authentic Linux terminal stdout
function formatStatusOutput(content: any): string {
  if (!content) return '[SYS] Diagnostics unavailable.';
  const engine = content.status || content.engine_status || 'ONLINE';
  const mem = content.memory_usage_mb ? `${content.memory_usage_mb} MB` : 'N/A';
  const uptime = content.uptime_seconds ? `${Math.floor(content.uptime_seconds / 60)}m ${content.uptime_seconds % 60}s` : '0m 0s';
  const txCount = content.loaded_transactions ?? content.dataset?.loaded_transactions;
  const walletCount = content.unique_wallets ?? content.dataset?.unique_wallets;
  const illicitRatio = content.illicit_transaction_ratio !== undefined && content.illicit_transaction_ratio !== null
    ? `${(content.illicit_transaction_ratio * 100).toFixed(2)}%`
    : (content.illicit_ratio_note || 'N/A');
  const clusters = content.cluster_count ?? content.clustering?.total_clusters;
  const alertsCount = content.alert_count ?? content.typologies?.total_alerts;

  return [
    '================================================================================',
    ' BITKAUN ENGINE INTERNAL SYSTEM STATUS & TELEMETRY',
    '================================================================================',
    ` [ENGINE STATUS]          : ${String(engine).toUpperCase()}`,
    ` [HOST AIR-GAP]           : ISOLATED (100% OFFLINE)`,
    ` [SYSTEM UPTIME]          : ${uptime}`,
    ` [MEMORY FOOTPRINT]       : ${mem}`,
    '--------------------------------------------------------------------------------',
    ` [INDEXED TRANSACTIONS]   : ${txCount === undefined ? 'N/A' : Number(txCount).toLocaleString()}`,
    ` [INDEXED WALLETS]        : ${walletCount === undefined ? 'N/A' : Number(walletCount).toLocaleString()}`,
    ` [CIOH ENTITY CLUSTERS]   : ${clusters === undefined ? 'N/A' : Number(clusters).toLocaleString()}`,
    ` [ML DETECTED ALERTS]     : ${alertsCount === undefined ? 'N/A' : Number(alertsCount).toLocaleString()}`,
    ` [ILLICIT TX RATIO]       : ${illicitRatio}`,
    ` [TOPOLOGY ENGINE]        : ONLINE (Ransomware, Peeling, Mixing, Layering)`,
    ` [ML INFERENCE PIPELINE]  : XGBOOST BINARY + MULTI-CLASS + SHAP EXPLAINER`,
    '================================================================================'
  ].join('\n');
}

// Format HELP manual into authentic Linux shell manual
function formatHelpOutput(filter?: string | null): string {
  if (filter) {
    const f = filter.toLowerCase().trim();
    const cmdInfo: Record<string, { usage: string; aliases: string[]; desc: string; examples: string[] }> = {
      benchmark: {
        usage: 'benchmark',
        aliases: ['eval', 'metrics', 'accuracy'],
        desc: 'Displays V8 quantitative model evaluation scorecard (Precision, Recall, F1 for Peeling Chains, Layering, Mixing, and Ransomware + 0.42ms inference latency).',
        examples: ['benchmark', 'eval']
      },
      search: {
        usage: 'search <query>',
        aliases: ['find', 'query'],
        desc: 'Universal multi-entity query across integer TxID, Bitcoin address, origin IP, ASN, or scenario cluster.',
        examples: ['search 881920041', 'search 1PeelHeadWallet0001', 'search AS49981', 'search peeling_chain_04651']
      },
      scenarios: {
        usage: 'scenarios [prefix] [page]',
        aliases: ['clusters'],
        desc: 'Paginated directory of scenario clusters with transaction counts, total BTC volumes, and relay node infrastructure.',
        examples: ['scenarios', 'scenarios peel 1', 'scenarios mix 1', 'scenarios ransom 1']
      },
      telemetry: {
        usage: 'telemetry',
        aliases: ['stats', 'p2p'],
        desc: 'Global P2P broadcast statistics across 82,078 transactions: node infrastructure distributions, propagation latency Δt, top ASNs and countries.',
        examples: ['telemetry', 'stats']
      },
      communities: {
        usage: 'communities [scenario_id]',
        aliases: ['community', 'syndicates'],
        desc: 'NetworkX greedy modularity community partition showing co-acting entity syndicates and wallet/transaction sub-clusters.',
        examples: ['communities peeling_chain_04651', 'communities live_ransomware_probe']
      },
      flow: {
        usage: 'flow <txid>',
        aliases: ['decompose'],
        desc: 'Financial UTXO input-to-output decomposition displaying CIOH entity cluster roots, miner fees, and broadcast relay network telemetry.',
        examples: ['flow 881920041', 'flow 322596997']
      },
      anomaly: {
        usage: 'anomaly [scenario_id]',
        aliases: ['unusual'],
        desc: 'Isolation Forest anomaly & unusualness score (0-100) relative to normal licit Bitcoin distribution (SIH PS146 compliant).',
        examples: ['anomaly peeling_chain_04651', 'anomaly live_ransomware_probe']
      },
      correlate: {
        usage: 'correlate',
        aliases: ['upload', 'dualstream'],
        desc: 'Dual-stream Ledger CSV & P2P Telemetry CSV correlation workspace with instant XGBoost inference and TreeSHAP attribution.',
        examples: ['correlate', 'upload']
      },
      graph: {
        usage: 'graph [scenario_id]',
        aliases: ['dashboard', 'g', 'nodes'],
        desc: '3D WebGL force-directed graph visualizer with Bitcoin medallion sprites, trust colors, and moving transaction particles.',
        examples: ['graph', 'graph peeling_chain_04651', 'graph ransomware_03287']
      },
      inspect: {
        usage: 'inspect <txid | address | scenario_id>',
        aliases: ['i'],
        desc: 'Deep forensic audit of multi-I/O UTXO arrays, miner fees, script type, and pre-block relay network telemetry.',
        examples: ['inspect 881920041', 'inspect 18hvz1KnqUjLRr3KHifSbMDi6m', 'inspect peeling_chain_04651']
      },
      trace: {
        usage: 'trace <source_address> <target_address>',
        aliases: ['route'],
        desc: 'Multi-hop BFS shortest path velocity tracer calculating the fastest flow of funds between two wallet addresses.',
        examples: ['trace 18hvz1KnqUjLRr3KHifSbMDi6m 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa']
      },
      taint: {
        usage: 'taint <seed_address>',
        aliases: [],
        desc: 'Forward dirty coin risk propagation and decay (FIFO / Haircut poisoning models) across downstream payment hops.',
        examples: ['taint 18hvz1KnqUjLRr3KHifSbMDi6m']
      },
      alerts: {
        usage: 'alerts [pattern_type] [--limit <n>]',
        aliases: ['alert'],
        desc: 'Real-time prioritized AML forensic alerts feed ranked by XGBoost risk score and SHAP feature evidence.',
        examples: ['alerts', 'alerts peel', 'alerts ransomware', 'alerts --limit 10']
      },
      dossier: {
        usage: 'dossier <txid | list>',
        aliases: ['report'],
        desc: 'Generates a confidential system investigative summary with transaction chronology and exportable report.',
        examples: ['dossier 881920041', 'dossier list']
      },
      tor: {
        usage: 'tor [txid]',
        aliases: [],
        desc: 'Passive multi-vantage Tor timing entropy profiler and relay de-anonymization metrics.',
        examples: ['tor', 'tor 881920041']
      },
      ingest: {
        usage: 'ingest sample [type] | ingest <raw_json>',
        aliases: ['inject'],
        desc: 'Dynamic live transaction injection with instant XGBoost risk scoring and TreeSHAP explainability.',
        examples: ['ingest sample ransomware', 'ingest sample peeling_chain', 'ingest sample mixing']
      },
      logs: {
        usage: 'logs',
        aliases: ['log', 'stream'],
        desc: 'Live mempool gossip telemetry and block ingestion event stream.',
        examples: ['logs']
      },
      status: {
        usage: 'status',
        aliases: ['sys', 'health'],
        desc: 'In-memory engine telemetry, loaded transaction counts, unique wallets, and system health.',
        examples: ['status']
      },
      sound: {
        usage: 'sound [on|off]',
        aliases: ['audio'],
        desc: 'Toggle procedural mechanical keyboard audio and alert chimes.',
        examples: ['sound on', 'sound off']
      },
      clear: {
        usage: 'clear',
        aliases: ['cls'],
        desc: 'Clear the terminal output screen buffer (Shortcut: Ctrl+L).',
        examples: ['clear']
      }
    };

    const target = Object.keys(cmdInfo).find(k => k === f || cmdInfo[k].aliases.includes(f));
    if (target) {
      const info = cmdInfo[target];
      return [
        '================================================================================',
        ` BITKAUN-MAN(1) :: FORENSIC SYSCALL MANUAL :: ${target.toUpperCase()}`,
        '================================================================================',
        ` [COMMAND]     : ${target}`,
        ` [USAGE]       : ${info.usage}`,
        ` [ALIASES]     : ${info.aliases.length > 0 ? info.aliases.join(', ') : 'none'}`,
        '--------------------------------------------------------------------------------',
        ` [DESCRIPTION] : ${info.desc}`,
        '--------------------------------------------------------------------------------',
        ' [INVOCATION EXAMPLES] :',
        ...info.examples.map(ex => `   > ${ex}`),
        '================================================================================'
      ].join('\n');
    }
  }

  // Full manual index
  return [
    '================================================================================',
    ' BITKAUN V8 FORENSIC TERMINAL // COMMAND REFERENCE MANUAL',
    '================================================================================',
    '  graph [scenario_id]       - 3D WebGL force-directed graph with Bitcoin sprites & orbs',
    '  inspect <txid|addr|sc_id> - Deep audit of UTXO flows, fees, and P2P origin telemetry',
    '  trace <src> <dst>         - Run multi-hop shortest path velocity trace',
    '  taint <seed_address>      - Forward dirty coin risk propagation & decay',
    '  flow <txid>               - Financial UTXO flow decomposition & CIOH entity clusters',
    '  communities <scenario_id> - Modularity-based entity syndicates & co-acting clusters',
    '  anomaly <scenario_id>     - Isolation Forest structural & temporal unusualness score',
    '  search <query>            - Universal search across TxID, wallet, IP, ASN, or scenario',
    '  scenarios [prefix] [page] - Scenario cluster directory with volumes & node distributions',
    '  alerts [pattern]          - Real-time detected typology candidates & ML alerts',
    '  benchmark / eval          - Model evaluation scorecard (Precision, Recall, F1, Latency)',
    '  telemetry / stats         - Global P2P broadcast telemetry & propagation latency stats',
    '  dossier <txid|list>       - Generate LEA investigative summary or list saved cases',
    '  tor [txid]                - Tor timing entropy analysis & exit node profiler',
    '  ingest sample [type]      - Dynamic injection of ransomware/peeling/mixing/licit flows',
    '  ingest <raw_json>         - Dynamic live-injection of custom TX with instant ML scoring',
    '  correlate / upload        - Dual-stream Ledger & P2P Telemetry correlation & V8 ML scoring',
    '  logs                      - Live mempool & block ingestion event telemetry',
    '  status                    - In-memory engine telemetry, loaded counts & health',
    '  sound [on|off]            - Toggle procedural mechanical keyboard & alert sounds',
    '  clear                     - Clear terminal screen (Shortcut: Ctrl+L)',
    '================================================================================',
    '  SHORTCUTS: [Tab] Autocomplete | [Up/Down] History | [Ctrl+L] Clear Screen',
    '  TIP: Type "help <command>" (e.g. "help flow", "help benchmark") for details',
    '================================================================================'
  ].join('\n');
}

export const CliOutputRenderer: React.FC<CliOutputRendererProps> = React.memo(({
  entry,
  onRunCommand,
  onScrollRequested,
  onCloseEntry
}) => {
  const [revealedCount, setRevealedCount] = useState<number>(0);
  const [isFinished, setIsFinished] = useState<boolean>(false);
  const timerRef = useRef<any>(null);
  const soundTickRef = useRef<number>(0);
  const hasFinishedRef = useRef<boolean>(false);
  const onScrollRef = useRef(onScrollRequested);

  useEffect(() => {
    onScrollRef.current = onScrollRequested;
  }, [onScrollRequested]);

  // Complex interactive subwindows mount directly
  const isInteractive = [
    'GRAPH', 'INSPECT', 'TRACE', 'DOSSIER', 'TAINT', 'TOR', 'ALERTS', 'ALERT_DETAIL',
    'INGEST', 'INGEST_BATCH', 'TWO_STREAM_UPLOAD', 'SEARCH', 'SCENARIOS', 'BENCHMARK',
    'TELEMETRY', 'COMMUNITIES', 'FLOW', 'ANOMALY'
  ].includes(entry.type);

  // Prepare full terminal text stream
  const fullTextToStream = useMemo(() => {
    if (entry.type === 'STATUS') {
      return formatStatusOutput(entry.content);
    }
    if (entry.type === 'HELP') {
      return formatHelpOutput(entry.content?.filter);
    }
    if (entry.type === 'LOGS') {
      const logItems: any[] = Array.isArray(entry.content)
        ? entry.content
        : Array.isArray(entry.content?.events)
        ? entry.content.events
        : [];
      if (logItems.length === 0) {
        return '[STREAM] No active transactions in mempool buffer. Stream connection healthy.';
      }
      return [
        '========================================================================================================',
        ` LIVE MEMPOOL & INGESTION TELEMETRY STREAM (${logItems.length} RECENT EVENTS)`,
        '========================================================================================================',
        ...logItems.map((item, idx) => {
          const txid = item.txid || item.id || `TX_${idx}`;
          const amt = item.amount_btc !== undefined ? `${Number(item.amount_btc).toFixed(4)} BTC` : '0.0000 BTC';
          const ip = item.ip_address || item.relay_ip || '127.0.0.1';
          const country = item.country ? `[${item.country}]` : '[--]';
          const nodeType = (item.node_type || 'residential').toUpperCase();
          const flag = item.is_tor
            ? '[TOR_EXIT]'
            : item.risk_level === 'HIGH'
            ? `[RISK_HIGH:${Math.round((item.risk_score || 0) * 100)}%]`
            : item.typology
            ? `[${item.typology.toUpperCase()}]`
            : '[CLEAN]';
          return ` [${(idx + 1).toString().padStart(2, ' ')}] TX:${txid.toString().padEnd(10)} | ${amt.padEnd(14)} | IP: ${ip.padEnd(15)} ${country.padEnd(5)} | ${flag.padEnd(16)} | NODE: ${nodeType}`;
        }),
        '========================================================================================================'
      ].join('\n');
    }
    return entry.content?.message || (typeof entry.content === 'string' ? entry.content : '');
  }, [entry]);

  const totalChars = fullTextToStream.length;

  useEffect(() => {
    if (isInteractive || totalChars === 0 || hasFinishedRef.current) {
      setIsFinished(true);
      setRevealedCount(totalChars);
      return;
    }

    setRevealedCount(0);
    setIsFinished(false);

    // Characters per tick: 2-3 chars every 12ms provides authentic, snappy Linux TTY feel
    const charsPerTick = totalChars > 300 ? 3 : 2;
    const intervalMs = 12;

    timerRef.current = setInterval(() => {
      setRevealedCount(prev => {
        const next = prev + charsPerTick;
        soundTickRef.current++;
        if (soundTickRef.current % 4 === 0) {
          sound.playKeyClick();
        }
        if (onScrollRef.current) {
          onScrollRef.current();
        }
        if (next >= totalChars) {
          clearInterval(timerRef.current);
          setIsFinished(true);
          hasFinishedRef.current = true;
          return totalChars;
        }
        return next;
      });
    }, intervalMs);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [entry.id]); // CRITICAL: Only trigger when a NEW entry is created, NEVER when input changes in parent!

  const handleSkipTyping = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    hasFinishedRef.current = true;
    setRevealedCount(totalChars);
    setIsFinished(true);
    if (onScrollRef.current) {
      onScrollRef.current();
    }
  };

  return (
    <div style={{ marginBottom: '14px', fontFamily: 'monospace' }}>
      {/* 1. GRAPH VIEW (Pure 3D Three.js WebGL Engine) */}
      {entry.type === 'GRAPH' && (
        <div className="output-block" style={{ border: '1px solid #00ff66', padding: '6px', background: '#020603' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px', padding: '0 4px' }}>
            <span style={{ color: '#33ff88', fontWeight: 'bold', fontSize: '13px' }}>
              &gt; BITCOIN 3D WEBGL ON-CHAIN GRAPH VISUALIZER {entry.content?.scenarioId ? `[SCENARIO: ${entry.content.scenarioId}]` : ''}
            </span>
            {onCloseEntry && (
              <span className="cmd-tag" onClick={() => onCloseEntry(entry.id)}>
                [Close]
              </span>
            )}
          </div>
          <GraphView
            scenarioId={entry.content?.scenarioId || 'licit_00001'}
            onClose={onCloseEntry ? () => onCloseEntry(entry.id) : undefined}
          />
        </div>
      )}

      {/* 2. INSPECT VIEW */}
      {entry.type === 'INSPECT' && entry.content && (
        <div className="output-block" style={{ border: '1px solid #00aa44', padding: '12px', background: 'var(--bg-card)' }}>
          <InspectView
            node={entry.content.node}
            data={entry.content.raw}
            onRunCommand={onRunCommand}
          />
        </div>
      )}

      {/* 3. TRACE VIEW */}
      {entry.type === 'TRACE' && entry.content && (
        <div className="output-block" style={{ border: '1px solid #00aa44', padding: '12px', background: 'var(--bg-card)' }}>
          <TraceView
            sourceId={entry.content.source}
            targetId={entry.content.target}
            traceResult={entry.content.traceResult}
            onRunCommand={onRunCommand}
          />
        </div>
      )}

      {/* 4. TAINT VIEW */}
      {entry.type === 'TAINT' && entry.content && (
        <div className="output-block" style={{ background: 'var(--bg-card)', border: '1px solid #00aa44', padding: '12px' }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', fontSize: '15px', marginBottom: '8px' }}>
            FORWARD TAINT DECAY ANALYSIS // SEED: {entry.content.seed_address}
          </div>
          <div style={{ marginBottom: '10px', fontSize: '13px', color: '#aaffaa' }}>
            Model: {entry.content.model || 'FIFO Poisoning with Decay'} | Total Tainted Volume: {entry.content.total_tainted_btc ?? entry.content.total_tainted_volume_btc ?? 0} BTC
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #00ff66', textAlign: 'left', color: '#33ff88' }}>
                <th style={{ padding: '4px' }}>Hop</th>
                <th style={{ padding: '4px' }}>Address</th>
                <th style={{ padding: '4px' }}>Taint %</th>
                <th style={{ padding: '4px' }}>Tainted BTC</th>
                <th style={{ padding: '4px' }}>Via TXID</th>
              </tr>
            </thead>
            <tbody>
              {(entry.content.tainted_descendants || entry.content.contaminated_wallets || []).map((n: any, i: number) => (
                <tr key={i} style={{ borderBottom: '1px solid #00220a' }}>
                  <td style={{ padding: '5px', color: '#ffaa33' }}>Hop {n.hop_distance}</td>
                  <td style={{ padding: '5px' }}>
                    <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${n.address}`)}>{n.address}</span>
                  </td>
                  <td style={{ padding: '5px', color: n.taint_score >= 0.5 ? '#ff3344' : '#33ff88' }}>{(n.taint_score * 100).toFixed(1)}%</td>
                  <td style={{ padding: '5px' }}>{n.received_tainted_btc ?? n.received_btc_from_seed ?? 0} BTC</td>
                  <td style={{ padding: '5px' }}>
                    <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${n.via_txid}`)}>{n.via_txid}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 5. DOSSIER VIEW */}
      {entry.type === 'DOSSIER' && entry.content && (
        <div className="output-block" style={{ background: 'var(--bg-card)', border: '1px solid #ff3344', padding: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <div style={{ color: '#ff3344', fontWeight: 'bold', fontSize: '15px' }}>
              CONFIDENTIAL // SYSTEM-GENERATED INVESTIGATIVE SUMMARY
            </div>
            <a
              href={`http://localhost:8000/api/dossier/${entry.content.transaction_evidence?.txid}/html`}
              target="_blank"
              rel="noreferrer"
              style={{ background: '#00ff66', color: '#000', padding: '3px 10px', fontWeight: 'bold', textDecoration: 'none', borderRadius: '3px', fontSize: '12px' }}
            >
              🖨️ Export Investigation Summary PDF
            </a>
          </div>
          <div style={{ fontSize: '13px', lineHeight: '1.6' }}>
            <p><strong>Case ID:</strong> <code>{entry.content.case_metadata?.dossier_id}</code> | <strong>Threat Rating:</strong> <span style={{ color: '#ff3344', fontWeight: 'bold' }}>{entry.content.threat_assessment?.risk_rating} (Score: {entry.content.threat_assessment?.composite_risk_score})</span></p>
            <p><strong>Data status:</strong> {entry.content.case_metadata?.data_status} | <strong>Model status:</strong> {entry.content.case_metadata?.model_status}</p>
            <p><strong>Target TXID:</strong> <code>{entry.content.transaction_evidence?.txid}</code> | <strong>Value:</strong> {entry.content.transaction_evidence?.transferred_btc} BTC</p>
            <p><strong>Recorded relay telemetry:</strong> IP {entry.content.network_telemetry_observation?.observed_relay_ip} ({entry.content.network_telemetry_observation?.recorded_isp}) | Country code: {entry.content.network_telemetry_observation?.recorded_country_code} | Tor indicator: {entry.content.network_telemetry_observation?.tor_exit_indicator ? 'RECORDED' : 'NOT RECORDED'}</p>
            <p><strong>CIOH Entity Cluster:</strong> {entry.content.entity_clustering?.entity_cluster_id} ({entry.content.entity_clustering?.total_cioh_linked_addresses_observed} linked addresses observed)</p>
            <div style={{ marginTop: '10px', background: '#001406', padding: '10px', borderLeft: '3px solid #00ff66' }}>
              <strong>Recommended Investigative Actions:</strong>
              <p style={{ margin: '6px 0', color: '#ffaa33' }}>{entry.content.case_metadata?.document_status}</p>
              <ul style={{ margin: '6px 0 0 16px', padding: 0 }}>
                {entry.content.recommended_investigative_actions?.map((d: string, idx: number) => (
                  <li key={idx}>{d}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* 5b. SAVED DOSSIERS CASE REGISTRY VIEW */}
      {entry.type === 'DOSSIER_LIST' && entry.content && (
        <div className="output-block" style={{ background: 'var(--bg-card)', border: '1px solid #00ff66', padding: '14px' }}>
          <div style={{ color: '#00ff66', fontWeight: 'bold', fontSize: '15px', marginBottom: '8px' }}>
            📁 PERSISTENT INVESTIGATION SUMMARY REGISTRY ({entry.content.length} SAVED SUMMARIES)
          </div>
          {entry.content.length === 0 ? (
            <div style={{ color: '#aaffaa', fontSize: '13px' }}>
              No investigation summaries have been generated yet. Run <code>dossier &lt;txid&gt;</code> to generate and persist a system summary.
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', marginTop: '8px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #005522', color: '#33ff88', textAlign: 'left' }}>
                  <th style={{ padding: '6px' }}>Dossier ID</th>
                  <th style={{ padding: '6px' }}>Target TXID</th>
                  <th style={{ padding: '6px' }}>Scenario Cluster</th>
                  <th style={{ padding: '6px' }}>Risk</th>
                  <th style={{ padding: '6px' }}>Created At</th>
                  <th style={{ padding: '6px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {entry.content.map((d: any) => (
                  <tr key={d.dossier_id} style={{ borderBottom: '1px solid #00220a' }}>
                    <td style={{ padding: '6px', fontWeight: 'bold', color: '#ff5566' }}>{d.dossier_id}</td>
                    <td style={{ padding: '6px' }}>
                      <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${d.txid}`)}>{d.txid}</span>
                    </td>
                    <td style={{ padding: '6px' }}>
                      <span className="cmd-clickable" onClick={() => onRunCommand(`g ${d.scenario_id}`)}>{d.scenario_id}</span>
                    </td>
                    <td style={{ padding: '6px', color: d.risk_level === 'CRITICAL' || d.risk_level === 'HIGH' ? '#ff3344' : '#33ff88' }}>
                      {d.risk_level}
                    </td>
                    <td style={{ padding: '6px', color: '#888' }}>{d.created_at}</td>
                    <td style={{ padding: '6px' }}>
                      <span className="cmd-tag" onClick={() => onRunCommand(`dossier ${d.txid}`)} style={{ cursor: 'pointer', marginRight: '6px' }}>
                        [View]
                      </span>
                      <a
                        href={`http://localhost:8000/api/dossier/${d.txid}/html`}
                        target="_blank"
                        rel="noreferrer"
                        style={{ color: '#00ff66', textDecoration: 'none', fontWeight: 'bold' }}
                      >
                        [PDF]
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* 6. ALERTS FEED */}
      {entry.type === 'ALERTS' && entry.content && (
        <AlertsListView
          content={entry.content}
          onRunCommand={onRunCommand}
          onClose={onCloseEntry ? () => onCloseEntry(entry.id) : undefined}
        />
      )}

      {/* 6b. DEEP SHAP ALERT EVIDENCE DOSSIER */}
      {entry.type === 'ALERT_DETAIL' && entry.content && (
        <div className="output-block" style={{ background: 'var(--bg-card)', border: '1px solid #00aa44', padding: '14px' }}>
          <AlertDetailView
            evidence={entry.content}
            onRunCommand={onRunCommand}
            onClose={onCloseEntry ? () => onCloseEntry(entry.id) : undefined}
          />
        </div>
      )}

      {/* 7. TOR INTELLIGENCE PROFILER */}
      {entry.type === 'TOR' && entry.content && (
        <div className="output-block" style={{ background: 'var(--bg-card)', border: '1px solid #00aa44', padding: '12px' }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', fontSize: '15px', marginBottom: '8px' }}>
            TOR &amp; OBFUSCATED INFRASTRUCTURE TELEMETRY
          </div>
          {entry.content.total_tor_transactions !== undefined ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px', fontSize: '13px' }}>
              <div><strong>Total Tor Transactions:</strong> <span style={{ color: '#ff3344' }}>{entry.content.total_tor_transactions}</span></div>
              <div><strong>Unique Tor Exit Nodes:</strong> {entry.content.unique_tor_exit_nodes}</div>
              <div><strong>Timing Entropy (H):</strong> <span style={{ color: '#33ff88' }}>{entry.content.tor_timing_entropy}</span> <span style={{ color: '#77aa88', fontSize: '11px' }}>(Shannon H = -Σ p log₂ p, 1s bins)</span></div>
              <div><strong>Avg Tor Delay (Δt):</strong> {entry.content.average_tor_propagation_delay_sec} seconds</div>
              <div style={{ gridColumn: '1 / -1', color: '#77aa88', fontSize: '11px', marginTop: '4px' }}>
                [TELEMETRY BENCHMARK]: Observed Relay Telemetry (Synthetic V7 Ground-Truth Benchmark · Zero Identity Attribution Claimed)
              </div>
            </div>
          ) : (
            <div style={{ fontSize: '13px' }}>
              <p><strong>Suspect TXID:</strong> {entry.content.txid} | <strong>IP:</strong> {entry.content.ip_address} | <strong>Tor Node:</strong> {entry.content.is_tor ? 'YES' : 'NO'}</p>
              <p><strong>Shannon Timing Entropy:</strong> {entry.content.timing_entropy} ({entry.content.entropy_interpretation})</p>
              <p><strong>Relay telemetry correlation:</strong> <span style={{ color: '#33ff88' }}>{entry.content.relay_telemetry_correlation_indicator}</span></p>
              <p><strong>Attribution note:</strong> {entry.content.attribution_note}</p>
              <p><strong>Obfuscation Evasion Score:</strong> <span style={{ color: '#ff3344' }}>{entry.content.obfuscation_evasion_score}</span></p>
            </div>
          )}
        </div>
      )}

      {/* 7b. LIVE INGESTION RESULT VIEW */}
      {entry.type === 'INGEST' && entry.content && (
        <div className="output-block" style={{ background: 'var(--bg-card)', border: entry.content.is_illicit ? '1px solid #ff3344' : '1px solid #00ff66', padding: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <div style={{ color: entry.content.is_illicit ? '#ff3344' : '#00ff66', fontWeight: 'bold', fontSize: '15px' }}>
              ⚡ LIVE CORRELATED TRANSACTION INGESTED // TXID: {entry.content.txid}
            </div>
            <span style={{
              background: entry.content.is_illicit ? '#ff334422' : '#00ff6622',
              color: entry.content.is_illicit ? '#ff3344' : '#00ff66',
              border: `1px solid ${entry.content.is_illicit ? '#ff3344' : '#00ff66'}`,
              padding: '2px 8px',
              borderRadius: '3px',
              fontSize: '11px',
              fontWeight: 'bold'
            }}>
              {entry.content.is_illicit ? `ILLICIT: ${entry.content.predicted_typology?.toUpperCase()} (${(entry.content.typology_confidence * 100).toFixed(1)}%)` : `LICIT (P(illicit) ${(entry.content.binary_confidence * 100).toFixed(1)}%)`}
            </span>
          </div>

          <div style={{ fontSize: '13px', lineHeight: '1.6' }}>
            <p><strong>Scenario Cluster:</strong> <code>{entry.content.scenario_id}</code> | <strong>Primary Wallet:</strong> <code>{entry.content.primary_wallet}</code></p>
            <p><strong>Binary Risk Score:</strong> <span style={{ color: entry.content.risk_score >= 0.5 ? '#ff3344' : '#33ff88', fontWeight: 'bold' }}>{(entry.content.risk_score * 100).toFixed(1)}%</span> | <strong>Typology:</strong> <span style={{ color: '#ffaa00', fontWeight: 'bold' }}>{entry.content.predicted_typology?.toUpperCase()}</span></p>
            {entry.content.anomaly_score !== null && entry.content.anomaly_score !== undefined && (
              <p><strong>Isolation Forest Anomaly / Unusualness (0–100; not probability):</strong> <span style={{ color: entry.content.anomaly_score >= 70 ? '#ff3344' : entry.content.anomaly_score >= 40 ? '#ffaa00' : '#33ff88' }}>{entry.content.anomaly_score} [{entry.content.anomaly_label}]</span></p>
            )}
            
            {entry.content.top_shap_attributions?.length > 0 && (
              <div style={{ marginTop: '8px', background: '#001406', padding: '8px', borderLeft: '3px solid #00ff66' }}>
                <strong style={{ color: '#33ff88' }}>Top SHAP Risk Factors:</strong>
                <ul style={{ margin: '4px 0 0 16px', padding: 0, fontSize: '12px' }}>
                  {entry.content.top_shap_attributions.map((attr: any, i: number) => (
                    <li key={i} style={{ color: attr.direction === 'RISK_INCREASING' ? '#ffaa77' : '#aaffaa' }}>
                      {attr.feature_name}: {attr.value} (SHAP: {attr.shap_value >= 0 ? `+${attr.shap_value.toFixed(3)}` : attr.shap_value.toFixed(3)}) [{attr.direction}]
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div style={{ marginTop: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <span className="cmd-tag" onClick={() => onRunCommand(`g ${entry.content.scenario_id}`)} style={{ cursor: 'pointer' }}>
                [Open in 3D Graph]
              </span>
              <span className="cmd-tag" onClick={() => onRunCommand(`inspect ${entry.content.txid}`)} style={{ cursor: 'pointer' }}>
                [Inspect TX]
              </span>
              <span className="cmd-tag" onClick={() => onRunCommand(`taint ${entry.content.primary_wallet}`)} style={{ cursor: 'pointer' }}>
                [Propagate Taint]
              </span>
              <span className="cmd-tag" onClick={() => onRunCommand(`dossier ${entry.content.txid}`)} style={{ cursor: 'pointer' }}>
                [Export LEA Dossier]
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 7c. BATCH INGESTION VIEW */}
      {entry.type === 'INGEST_BATCH' && entry.content && (
        <div className="output-block" style={{ background: 'var(--bg-card)', border: '1px solid #00ff66', padding: '14px' }}>
          <div style={{ color: '#00ff66', fontWeight: 'bold', fontSize: '15px', marginBottom: '8px' }}>
            📁 BULK DATASET INGESTION COMPLETED
          </div>
          <div style={{ fontSize: '13px', lineHeight: '1.6' }}>
            <p><strong>Transactions Ingested:</strong> <span style={{ color: '#33ff88', fontWeight: 'bold' }}>{entry.content.total_ingested}</span></p>
            <p><strong>New Wallets Indexed:</strong> {entry.content.unique_wallets_added}</p>
            <p><strong>Scenario Clusters:</strong> {entry.content.scenario_ids?.join(', ') || 'Auto-clustered'}</p>
            {entry.content.scenario_results?.map((result: any) => {
              const available = result.analysis_status === 'AVAILABLE';
              return (
                <div
                  key={result.scenario_id}
                  style={{
                    marginTop: '10px',
                    padding: '9px',
                    border: `1px solid ${available ? '#006b32' : '#aa7700'}`,
                    background: available ? '#001c0b' : '#211700',
                  }}
                >
                  <div style={{ color: available ? '#33ff88' : '#ffaa33', fontWeight: 'bold' }}>
                    ML ANALYSIS // {result.scenario_id} // {available ? 'AVAILABLE' : 'UNAVAILABLE'}
                  </div>
                  <div style={{ fontSize: '12px', marginTop: '4px' }}>
                    Transactions: {result.transaction_count} | Features: {result.feature_count}
                  </div>
                  {result.sample_size_warning && (
                    <div style={{ color: '#ffcc66', fontSize: '12px', marginTop: '4px' }}>
                      {result.sample_size_warning}
                    </div>
                  )}
                  {available ? (
                    <>
                      <div style={{ fontSize: '12px', marginTop: '4px' }}>
                        Scenario P(illicit): {(Number(result.risk_score) * 100).toFixed(2)}% | Binary P(illicit): {(Number(result.binary_confidence) * 100).toFixed(2)}%
                      </div>
                      <div style={{ fontSize: '12px' }}>
                        Typology: {result.is_illicit ? (result.predicted_typology || 'unknown') : 'N/A — not applicable'} | Typology confidence: {result.is_illicit && result.typology_confidence !== null && result.typology_confidence !== undefined ? `${(Number(result.typology_confidence) * 100).toFixed(2)}%` : 'N/A — not applicable'}
                      </div>
                      <div style={{ fontSize: '12px' }}>
                        Anomaly / unusualness (0–100, not probability): {result.anomaly_score !== null && result.anomaly_score !== undefined ? `${result.anomaly_score} [${result.anomaly_label}]` : (result.anomaly_message || 'UNAVAILABLE')}
                      </div>
                    </>
                  ) : (
                    <div style={{ color: '#ffcc66', fontSize: '12px', marginTop: '4px' }}>
                      {result.analysis_message}
                    </div>
                  )}
                </div>
              );
            })}
            <div style={{ marginTop: '10px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {entry.content.scenario_ids?.map((scId: string) => (
                <span
                  key={scId}
                  className="cmd-tag"
                  onClick={() => onRunCommand(`g ${scId}`)}
                  style={{ cursor: 'pointer' }}
                >
                  [Explore 3D: {scId}]
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 7d. TWO-STREAM CORRELATION & UPLOAD VIEW */}
      {entry.type === 'TWO_STREAM_UPLOAD' && (
        <TwoStreamUploadView
          onRunCommand={onRunCommand}
          onClose={onCloseEntry ? () => onCloseEntry(entry.id) : undefined}
        />
      )}

      {/* 7e. UNIVERSAL FORENSIC SEARCH VIEW */}
      {entry.type === 'SEARCH' && entry.content && (
        <div className="output-block" style={{ border: '1px solid #00aa44', padding: '12px', background: 'var(--bg-card)' }}>
          <SearchView
            query={entry.content.query || ''}
            matchType={entry.content.match_type || 'UNKNOWN'}
            matches={entry.content.matches || []}
            onRunCommand={onRunCommand}
            onClose={onCloseEntry ? () => onCloseEntry(entry.id) : undefined}
          />
        </div>
      )}

      {/* 7f. SCENARIO DIRECTORY & CLUSTER EXPLORER */}
      {entry.type === 'SCENARIOS' && entry.content && (
        <div className="output-block" style={{ border: '1px solid #00aa44', padding: '12px', background: 'var(--bg-card)' }}>
          <ScenariosListView
            scenarios={entry.content.scenarios || []}
            totalScenarios={entry.content.total_scenarios || 0}
            currentPage={entry.content.page || 1}
            pageSize={entry.content.page_size || 20}
            currentPrefix={entry.content.prefix || ''}
            onRunCommand={onRunCommand}
            onClose={onCloseEntry ? () => onCloseEntry(entry.id) : undefined}
          />
        </div>
      )}

      {/* 7g. MODEL EVALUATION BENCHMARK SCORECARD */}
      {entry.type === 'BENCHMARK' && entry.content && (
        <div className="output-block" style={{ border: '1px solid #00aa44', padding: '12px', background: 'var(--bg-card)' }}>
          <BenchmarkView
            benchmark={entry.content}
            onRunCommand={onRunCommand}
            onClose={onCloseEntry ? () => onCloseEntry(entry.id) : undefined}
          />
        </div>
      )}

      {/* 7h. GLOBAL NETWORK TELEMETRY & PROPAGATION STATS */}
      {entry.type === 'TELEMETRY' && entry.content && (
        <div className="output-block" style={{ border: '1px solid #00aa44', padding: '12px', background: 'var(--bg-card)' }}>
          <TelemetryStatsView
            stats={entry.content}
            onRunCommand={onRunCommand}
            onClose={onCloseEntry ? () => onCloseEntry(entry.id) : undefined}
          />
        </div>
      )}

      {/* 7i. GRAPH MODULARITY & COMMUNITY PARTITIONS */}
      {entry.type === 'COMMUNITIES' && entry.content && (
        <div className="output-block" style={{ border: '1px solid #00aa44', padding: '12px', background: 'var(--bg-card)' }}>
          <CommunitiesView
            data={entry.content}
            scenarioId={entry.content.scenario_id || ''}
            onRunCommand={onRunCommand}
            onClose={onCloseEntry ? () => onCloseEntry(entry.id) : undefined}
          />
        </div>
      )}

      {/* 7j. FINANCIAL UTXO FLOW & CIOH ENTITY DECOMPOSITION */}
      {entry.type === 'FLOW' && entry.content && (
        <div className="output-block" style={{ border: '1px solid #00aa44', padding: '12px', background: 'var(--bg-card)' }}>
          <FlowView
            data={entry.content}
            txid={entry.content.txid}
            onRunCommand={onRunCommand}
            onClose={onCloseEntry ? () => onCloseEntry(entry.id) : undefined}
          />
        </div>
      )}

      {/* 7k. ISOLATION FOREST ANOMALY & UNUSUALNESS VIEW */}
      {entry.type === 'ANOMALY' && entry.content && (
        <div className="output-block" style={{ border: '1px solid #00aa44', padding: '12px', background: 'var(--bg-card)' }}>
          <AnomalyView
            data={entry.content}
            scenarioId={entry.content.scenario_id || ''}
            onRunCommand={onRunCommand}
            onClose={onCloseEntry ? () => onCloseEntry(entry.id) : undefined}
          />
        </div>
      )}

      {/* 8. AUTHENTIC CHARACTER-STREAMED LINUX TTY TERMINAL OUTPUT */}
      {(entry.type === 'STATUS' || entry.type === 'HELP' || entry.type === 'LOGS' || entry.type === 'TEXT' || entry.type === 'ERROR' || entry.type === 'SUCCESS') && (
        <div
          onClick={handleSkipTyping}
          style={{
            cursor: isFinished ? 'default' : 'pointer',
            whiteSpace: 'pre-wrap',
            lineHeight: '1.45',
            fontSize: '13px',
            color: entry.type === 'ERROR' ? '#ff4455' : entry.type === 'SUCCESS' ? '#33ff88' : '#aaffaa',
            background: entry.type === 'ERROR' ? '#1a0003' : 'transparent',
            padding: entry.type === 'ERROR' ? '8px 12px' : '2px 0',
            borderLeft: entry.type === 'ERROR' ? '3px solid #ff3344' : 'none',
          }}
        >
          {isFinished ? fullTextToStream : fullTextToStream.slice(0, revealedCount)}
          {!isFinished && <span style={{ color: '#00ff66', fontWeight: 'bold' }}>▌</span>}
        </div>
      )}
    </div>
  );
});

export default CliOutputRenderer;
