import React, { useState, useEffect, useRef, useMemo } from 'react';
import { ForensicNode, ForensicLink, KernelLogEntry } from '../types/terminal';
import { sound } from '../audio/soundEngine';
import GraphView from '../graph/components/GraphView';
import { InspectView } from './views/InspectView';
import { TraceView } from './views/TraceView';

export interface TerminalEntry {
  id: string;
  command?: string;
  type: 'BANNER' | 'TEXT' | 'ERROR' | 'SUCCESS' | 'HELP' | 'INSPECT' | 'TRACE' | 'LOGS' | 'GRAPH' | 'STATUS' | 'ALERTS' | 'TAINT' | 'DOSSIER' | 'TOR';
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
  const loadedTx = content?.loaded_transactions ?? content?.dataset?.loaded_transactions;
  const uniqueWallets = content?.unique_wallets ?? content?.dataset?.unique_wallets;
  const uniqueScenarios = content?.unique_scenarios ?? content?.dataset?.unique_scenarios;
  const uptime = content?.uptime_seconds ?? content?.dataset?.uptime_seconds;
  const clusters = content?.clustering?.total_clusters;
  const alertsCount = content?.typologies?.total_alerts;
  const mlModel = content?.ml_model?.model_type;

  return [
    '================================================================================',
    ' BITKAUN BACKEND FORENSIC ENGINE DIAGNOSTICS // SYSTEM RUNTIME REPORT',
    '================================================================================',
    ` [ENGINE STATUS]          : ${content?.status || 'ONLINE (FastAPI 100% Offline)'}`,
    ` [TRANSACTIONS INDEXED]   : ${loadedTx !== undefined ? Number(loadedTx).toLocaleString() : 'Feature not implemented (intended feature: "Live ledger transaction count")'}`,
    ` [UNIQUE WALLETS]         : ${uniqueWallets !== undefined ? Number(uniqueWallets).toLocaleString() : 'Feature not implemented (intended feature: "Unique wallet indexing count")'}`,
    ` [UNIQUE SCENARIOS]       : ${uniqueScenarios !== undefined ? Number(uniqueScenarios).toLocaleString() : 'Feature not implemented (intended feature: "Scenario cluster count")'}`,
    ` [CIOH ENTITY CLUSTERS]   : ${clusters !== undefined ? Number(clusters).toLocaleString() : 'Feature not implemented (intended feature: "CIOH cluster partition count")'}`,
    ` [TYPOLOGY ALERTS CACHED] : ${alertsCount !== undefined ? Number(alertsCount).toLocaleString() : 'Feature not implemented (intended feature: "ML typology alert count")'}`,
    ` [ML INFERENCE PIPELINE]  : ${mlModel || 'XGBoost v7 Production (Binary + Typology)'}`,
    ` [SYSTEM PROCESS UPTIME]  : ${uptime !== undefined ? Number(uptime).toFixed(1) + 's' : 'Feature not implemented (intended feature: "Engine process uptime")'}`,
    '================================================================================'
  ].join('\n');
}

// Format HELP manual into authentic Linux shell manual
function formatHelpOutput(): string {
  return [
    '================================================================================',
    ' BITKAUN HOLMES FORENSIC TERMINAL // COMMAND REFERENCE MANUAL',
    '================================================================================',
    '  graph [scenario_id]   - 3D WebGL force-directed graph with Bitcoin sprites & orbs',
    '  inspect <txid|addr>   - Deep audit of UTXO flows, fees, and P2P origin telemetry',
    '  trace <src> <dst>     - Run multi-hop shortest path velocity trace',
    '  taint <seed_address>  - Forward dirty coin risk propagation & decay',
    '  alerts                - Real-time detected typology candidates & ML alerts',
    '  dossier <txid>        - Generate court-admissible Section 91 Cr.P.C. legal dossier',
    '  tor [txid]            - Tor timing entropy analysis & exit node profiler',
    '  logs                  - Live mempool & block ingestion event telemetry',
    '  status                - In-memory engine telemetry, loaded counts & health',
    '  sound [on|off]        - Toggle procedural mechanical keyboard & alert sounds',
    '  clear                 - Clear terminal screen (Shortcut: Ctrl+L)',
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
  const isInteractive = ['GRAPH', 'INSPECT', 'TRACE', 'DOSSIER', 'TAINT', 'TOR', 'ALERTS'].includes(entry.type);

  // Prepare full terminal text stream
  const fullTextToStream = useMemo(() => {
    if (entry.type === 'STATUS') {
      return formatStatusOutput(entry.content);
    }
    if (entry.type === 'HELP') {
      return formatHelpOutput();
    }
    if (entry.type === 'LOGS') {
      const logItems: any[] = Array.isArray(entry.content) ? entry.content : [];
      if (logItems.length === 0) {
        return '[STREAM] No active transactions in mempool buffer. Stream connection healthy.';
      }
      return [
        '================================================================================',
        ` LIVE MEMPOOL & INGESTION TELEMETRY STREAM (${logItems.length} RECENT EVENTS)`,
        '================================================================================',
        ...logItems.map((item, idx) => {
          const txid = item.txid || item.id || `TX_${idx}`;
          const amt = item.amount_btc !== undefined ? `${item.amount_btc} BTC` : '0.00 BTC';
          const ip = item.relay_ip || '127.0.0.1';
          const flag = item.is_tor ? '[TOR_EXIT]' : item.typology ? `[${item.typology.toUpperCase()}]` : '[CLEAN]';
          return ` [${idx + 1}] TX:${txid.toString().padEnd(10)} | ${amt.padEnd(12)} | IP: ${ip.padEnd(15)} | ${flag}`;
        }),
        '================================================================================'
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
              CONFIDENTIAL // LAW ENFORCEMENT INVESTIGATION DOSSIER
            </div>
            <a
              href={`http://localhost:8000/api/dossier/${entry.content.transaction_evidence?.txid}/html`}
              target="_blank"
              rel="noreferrer"
              style={{ background: '#00ff66', color: '#000', padding: '3px 10px', fontWeight: 'bold', textDecoration: 'none', borderRadius: '3px', fontSize: '12px' }}
            >
              🖨️ Export Section 91 CrPC PDF
            </a>
          </div>
          <div style={{ fontSize: '13px', lineHeight: '1.6' }}>
            <p><strong>Case ID:</strong> <code>{entry.content.case_metadata?.dossier_id}</code> | <strong>Threat Rating:</strong> <span style={{ color: '#ff3344', fontWeight: 'bold' }}>{entry.content.threat_assessment?.risk_rating} (Score: {entry.content.threat_assessment?.composite_risk_score})</span></p>
            <p><strong>Target TXID:</strong> <code>{entry.content.transaction_evidence?.txid}</code> | <strong>Value:</strong> {entry.content.transaction_evidence?.btc_value} BTC</p>
            <p><strong>Relay Telemetry:</strong> IP {entry.content.network_telemetry_attribution?.ip_address} ({entry.content.network_telemetry_attribution?.isp}) | Country: {entry.content.network_telemetry_attribution?.country} | Tor: {entry.content.network_telemetry_attribution?.is_tor_exit_node ? 'YES (High Risk)' : 'NO'}</p>
            <p><strong>CIOH Entity Cluster:</strong> {entry.content.entity_clustering?.entity_cluster_id} ({entry.content.entity_clustering?.total_unmasked_wallets_in_cluster} co-owned wallets)</p>
            <div style={{ marginTop: '10px', background: '#001406', padding: '10px', borderLeft: '3px solid #00ff66' }}>
              <strong>Mandated Legal Directives:</strong>
              <ul style={{ margin: '6px 0 0 16px', padding: 0 }}>
                {entry.content.statutory_legal_directives?.map((d: string, idx: number) => (
                  <li key={idx}>{d}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* 6. ALERTS VIEW */}
      {entry.type === 'ALERTS' && entry.content && (() => {
        const alertList: any[] = Array.isArray(entry.content)
          ? entry.content
          : (entry.content.alerts || []);
        return (
          <div className="output-block" style={{ background: 'var(--bg-card)', border: '1px solid #00aa44', padding: '12px' }}>
            <div style={{ color: '#33ff88', fontWeight: 'bold', fontSize: '15px', marginBottom: '8px' }}>
              DETECTED TYPOLOGY ALERTS &amp; SYNDICATE CANDIDATES ({alertList.length} ALERTS)
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {alertList.slice(0, 10).map((alt: any) => (
                <div key={alt.candidate_id} style={{ border: '1px solid #004d20', padding: '8px', background: '#000c04' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: alt.severity === 'CRITICAL' ? '#ff3344' : '#ffaa00', fontWeight: 'bold' }}>
                      [{alt.severity}] {alt.predicted_pattern_type?.toUpperCase()}
                    </span>
                    <span style={{ color: '#33ff88' }}>Confidence: {(alt.confidence * 100).toFixed(1)}%</span>
                  </div>
                  <div style={{ fontSize: '13px', color: '#aaffaa', margin: '4px 0' }}>{alt.explanation}</div>
                  <div style={{ fontSize: '12px', color: '#66aa77' }}>
                    Primary Wallet: <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${alt.primary_wallet}`)}>{alt.primary_wallet}</span> | Scenario: <span className="cmd-clickable" onClick={() => onRunCommand(`graph ${alt.scenario_id}`)}>{alt.scenario_id}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })()}

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
              <div><strong>Timing Entropy (H):</strong> <span style={{ color: '#33ff88' }}>{entry.content.tor_timing_entropy}</span></div>
              <div><strong>Avg Tor Delay (Δt):</strong> {entry.content.average_tor_propagation_delay_sec}s</div>
            </div>
          ) : (
            <div style={{ fontSize: '13px' }}>
              <p><strong>Suspect TXID:</strong> {entry.content.txid} | <strong>IP:</strong> {entry.content.ip_address} | <strong>Tor Node:</strong> {entry.content.is_tor ? 'YES' : 'NO'}</p>
              <p><strong>Shannon Timing Entropy:</strong> {entry.content.timing_entropy} ({entry.content.entropy_interpretation})</p>
              <p><strong>Deanonymization Status:</strong> <span style={{ color: '#33ff88' }}>{entry.content.deanonymization_confidence}</span></p>
              <p><strong>Obfuscation Evasion Score:</strong> <span style={{ color: '#ff3344' }}>{entry.content.obfuscation_evasion_score}</span></p>
            </div>
          )}
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

