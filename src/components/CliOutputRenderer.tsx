import React, { useState, useEffect, useRef } from 'react';
import { ForensicNode, ForensicLink, KernelLogEntry } from '../types/terminal';
import { COMMAND_REGISTRY } from '../data/mockForensicData';
import { sound } from '../audio/soundEngine';
import { InspectView } from './views/InspectView';
import { TraceView } from './views/TraceView';
import { GraphView3D } from './views/GraphView3D';

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

export const CliOutputRenderer: React.FC<CliOutputRendererProps> = ({
  entry,
  onRunCommand,
  nodes = [],
  links = [],
  logs = [],
  onScrollRequested,
  onCloseEntry
}) => {
  const [revealedCount, setRevealedCount] = useState<number>(0);
  const [isFinished, setIsFinished] = useState<boolean>(false);
  const soundTickRef = useRef<number>(0);

  // For complex interactive subwindows (GRAPH, INSPECT, TRACE), display immediately
  const isInteractive = ['GRAPH', 'INSPECT', 'TRACE', 'DOSSIER', 'TAINT', 'TOR', 'ALERTS'].includes(entry.type);

  let totalSteps = 1;
  if (entry.type === 'HELP') {
    totalSteps = COMMAND_REGISTRY.length + 1;
  } else if (entry.type === 'STATUS') {
    totalSteps = 6;
  } else if (entry.type === 'LOGS') {
    totalSteps = Math.min(logs.length, 12) + 1;
  } else if (entry.type === 'ERROR' || entry.type === 'SUCCESS' || entry.type === 'TEXT') {
    const msg = entry.content?.message || '';
    totalSteps = Math.max(msg.length, 1);
  }

  useEffect(() => {
    if (isFinished || isInteractive) {
      setIsFinished(true);
      return;
    }

    onScrollRequested();

    const startDelay = setTimeout(() => {
      if (entry.type === 'ERROR' || entry.type === 'SUCCESS' || entry.type === 'TEXT') {
        const charInterval = 18;
        const timer = setInterval(() => {
          setRevealedCount(prev => {
            const next = prev + 1;
            soundTickRef.current++;
            if (soundTickRef.current % 2 === 0) {
              sound.playKeyClick();
            }
            onScrollRequested();
            if (next >= totalSteps) {
              clearInterval(timer);
              setIsFinished(true);
              return totalSteps;
            }
            return next;
          });
        }, charInterval);
        return () => clearInterval(timer);
      }

      const lineInterval = 60;
      const timer = setInterval(() => {
        setRevealedCount(prev => {
          const next = prev + 1;
          sound.playKeyClick();
          onScrollRequested();
          if (next >= totalSteps) {
            clearInterval(timer);
            setIsFinished(true);
            return totalSteps;
          }
          return next;
        });
      }, lineInterval);

      return () => clearInterval(timer);
    }, 100);

    return () => clearTimeout(startDelay);
  }, [entry.type, totalSteps, isFinished, isInteractive, onScrollRequested]);

  return (
    <div style={{ marginBottom: '16px' }}>
      {/* 1. GRAPH VIEW */}
      {entry.type === 'GRAPH' && (
        <div className="output-block" style={{ border: '1px solid var(--border-mid)', padding: '6px', background: '#000804' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px', padding: '0 4px' }}>
            <span style={{ color: '#33ff88', fontWeight: 'bold' }}>
              &gt; BITCOIN ON-CHAIN FORENSIC GRAPH VISUALIZER {entry.content?.scenarioId ? `[SCENARIO: ${entry.content.scenarioId}]` : ''}
            </span>
            {onCloseEntry && (
              <span className="cmd-tag" onClick={() => onCloseEntry(entry.id)}>
                [Close]
              </span>
            )}
          </div>
          <GraphView3D
            nodes={nodes}
            links={links}
            scenarioId={entry.content?.scenarioId || 'normal_00001'}
            onSelectNode={(id) => onRunCommand(`inspect ${id}`)}
            onRunCommand={onRunCommand}
          />
        </div>
      )}

      {/* 2. INSPECT VIEW */}
      {entry.type === 'INSPECT' && (
        <div className="output-block" style={{ border: '1px solid var(--border-mid)', padding: '10px', background: 'var(--bg-card)' }}>
          <InspectView
            node={entry.content?.node || { id: entry.content?.id || 'Unknown', label: 'Inspected Entity', type: 'WALLET', riskScore: 50, clusterId: 'entity_0', balanceBtc: 0, txCount: 0, firstSeen: '', lastSeen: '', tags: [], flags: [] }}
            data={entry.content?.raw}
            onRunCommand={onRunCommand}
          />
        </div>
      )}

      {/* 3. MULTI-HOP TRACE STREAM */}
      {entry.type === 'TRACE' && (
        <div className="output-block" style={{ border: '1px solid var(--border-mid)', padding: '10px', background: 'var(--bg-card)' }}>
          <TraceView
            sourceId={entry.content?.source || 'Source'}
            targetId={entry.content?.target || 'Target'}
            traceResult={entry.content?.traceResult}
            onRunCommand={onRunCommand}
          />
        </div>
      )}

      {/* 4. TAINT PROPAGATION VIEW */}
      {entry.type === 'TAINT' && entry.content && (
        <div className="output-block" style={{ color: 'var(--fg-text)', background: 'var(--bg-card)', padding: '12px', border: '1px solid var(--border-dim)' }}>
          <div style={{ color: 'var(--fg-primary)', fontWeight: 700, fontSize: '16px', marginBottom: '8px' }}>
            DIRTY COIN TAINT PROPAGATION (HAIRCUT / FIFO MODEL) :: {entry.content.seed_address}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px', marginBottom: '12px' }}>
            <div><strong>Contaminated Wallets:</strong> <span style={{ color: '#ff3344' }}>{entry.content.total_tainted_wallets}</span></div>
            <div><strong>Total Volume Tainted:</strong> <span style={{ color: '#33ff88' }}>{entry.content.total_tainted_volume_btc} BTC</span></div>
            <div><strong>Distance Decay Rate:</strong> {entry.content.decay_rate}</div>
            <div><strong>Max BFS Depth:</strong> {entry.content.max_depth} hops</div>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ background: '#00220a', color: '#33ff88', textAlign: 'left' }}>
                <th style={{ padding: '6px', border: '1px solid #004d20' }}>Hop Distance</th>
                <th style={{ padding: '6px', border: '1px solid #004d20' }}>Contaminated Wallet</th>
                <th style={{ padding: '6px', border: '1px solid #004d20' }}>Taint Risk Score</th>
                <th style={{ padding: '6px', border: '1px solid #004d20' }}>Tainted BTC Received</th>
                <th style={{ padding: '6px', border: '1px solid #004d20' }}>Via TXID</th>
              </tr>
            </thead>
            <tbody>
              {entry.content.contaminated_wallets?.slice(0, 10).map((n: any, i: number) => (
                <tr key={i} style={{ borderBottom: '1px solid #00220a' }}>
                  <td style={{ padding: '6px', color: '#ffaa33' }}>Hop {n.hop_distance}</td>
                  <td style={{ padding: '6px' }}>
                    <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${n.address}`)}>{n.address}</span>
                  </td>
                  <td style={{ padding: '6px', color: n.taint_score >= 0.5 ? '#ff3344' : '#33ff88' }}>{(n.taint_score * 100).toFixed(1)}%</td>
                  <td style={{ padding: '6px' }}>{n.received_tainted_btc} BTC</td>
                  <td style={{ padding: '6px' }}>
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
        <div className="output-block" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-mid)', padding: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <div style={{ color: '#ff3344', fontWeight: 'bold', fontSize: '15px' }}>
              CONFIDENTIAL // LAW ENFORCEMENT INVESTIGATION DOSSIER
            </div>
            <a
              href={`http://localhost:8000/api/dossier/${entry.content.transaction_evidence?.txid}/html`}
              target="_blank"
              rel="noreferrer"
              style={{ background: '#00ff66', color: '#000', padding: '4px 12px', fontWeight: 'bold', textDecoration: 'none', borderRadius: '3px', fontSize: '13px' }}
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

      {/* 6. ALERTS FEED */}
      {entry.type === 'ALERTS' && entry.content && (() => {
        const alertList: any[] = Array.isArray(entry.content)
          ? entry.content
          : (entry.content.alerts || []);
        return (
          <div className="output-block" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-dim)', padding: '12px' }}>
            <div style={{ color: '#33ff88', fontWeight: 'bold', fontSize: '16px', marginBottom: '8px' }}>
              DETECTED TYPOLOGY ALERTS &amp; SYNDICATE CANDIDATES ({alertList.length} ALERTS)
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {alertList.slice(0, 10).map((alt: any) => (
                <div key={alt.candidate_id} style={{ border: '1px solid #004d20', padding: '8px', background: '#000c04' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: alt.severity === 'CRITICAL' ? '#ff3344' : '#ffaa00', fontWeight: 'bold' }}>
                      [{alt.severity}] {alt.predicted_pattern_type?.toUpperCase()}
                    </span>
                    <span style={{ color: '#33ff88' }}>
                      Binary: {(alt.binary_confidence * 100).toFixed(1)}% | Typology: {(alt.typology_confidence * 100).toFixed(1)}%
                    </span>
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
        <div className="output-block" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-dim)', padding: '12px' }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', fontSize: '16px', marginBottom: '8px' }}>
            TOR &amp; OBFUSCATED INFRASTRUCTURE TELEMETRY
          </div>
          {entry.content.total_tor_transactions !== undefined ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px' }}>
              <div><strong>Total Tor Transactions:</strong> <span style={{ color: '#ff3344' }}>{entry.content.total_tor_transactions}</span></div>
              <div><strong>Unique Tor Exit Nodes:</strong> {entry.content.unique_tor_exit_nodes}</div>
              <div><strong>Timing Entropy (H):</strong> <span style={{ color: '#33ff88' }}>{entry.content.tor_timing_entropy}</span></div>
              <div><strong>Avg Tor Delay (Δt):</strong> {entry.content.average_tor_propagation_delay_sec}s</div>
            </div>
          ) : (
            <div>
              <p><strong>Suspect TXID:</strong> {entry.content.txid} | <strong>IP:</strong> {entry.content.ip_address} | <strong>Tor Node:</strong> {entry.content.is_tor ? 'YES' : 'NO'}</p>
              <p><strong>Shannon Timing Entropy:</strong> {entry.content.timing_entropy} ({entry.content.entropy_interpretation})</p>
              <p><strong>Deanonymization Status:</strong> <span style={{ color: '#33ff88' }}>{entry.content.deanonymization_confidence}</span></p>
              <p><strong>Obfuscation Evasion Score:</strong> <span style={{ color: '#ff3344' }}>{entry.content.obfuscation_evasion_score}</span></p>
            </div>
          )}
        </div>
      )}

      {/* 8. STATUS STREAM */}
      {entry.type === 'STATUS' && (
        <div className="output-block" style={{ color: 'var(--fg-text)', background: 'var(--bg-card)', padding: '12px', border: '1px solid var(--border-dim)' }}>
          <div style={{ color: 'var(--fg-primary)', fontWeight: 700, marginBottom: '6px', fontSize: '16px' }}>
            BITKAUN BACKEND FORENSIC ENGINE DIAGNOSTICS
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '8px', fontSize: '14px' }}>
            <div>• <strong>Engine Status:</strong> <span style={{ color: '#33ff88' }}>ONLINE (FastAPI 100% Offline)</span></div>
            <div>• <strong>Transactions Indexed:</strong> {entry.content?.dataset?.loaded_transactions?.toLocaleString() || 'UNAVAILABLE'}</div>
            <div>• <strong>Unique Wallets:</strong> {entry.content?.dataset?.unique_wallets?.toLocaleString() || 'UNAVAILABLE'}</div>
            <div>• <strong>Entity Clusters Partitioned:</strong> {entry.content?.clustering?.total_clusters?.toLocaleString() || 'UNAVAILABLE'}</div>
            <div>• <strong>Typology Alerts Cached:</strong> {entry.content?.typologies?.total_alerts?.toLocaleString() || 'UNAVAILABLE'}</div>
            <div>• <strong>ML Inference Model:</strong> <span style={{ color: '#33ff88' }}>{entry.content?.ml_model?.model_type || 'XGBoost V7 candidate'}</span></div>
          </div>
        </div>
      )}

      {/* 9. HELP MANUAL */}
      {entry.type === 'HELP' && (
        <div className="output-block" style={{ color: 'var(--fg-text)', background: 'var(--bg-card)', padding: '12px', border: '1px solid var(--border-dim)' }}>
          <div style={{ color: 'var(--fg-primary)', fontWeight: 700, marginBottom: '8px', fontSize: '16px' }}>
            AVAILABLE FORENSIC COMMANDS
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '14px' }}>
            <div><span className="cmd-tag" onClick={() => onRunCommand('graph')}>graph [scenario_id]</span> - Open interactive 3D WebGL / 2D link-analysis graph</div>
            <div><span className="cmd-tag" onClick={() => onRunCommand('inspect 58234917')}>inspect &lt;txid|address&gt;</span> - Inspect on-chain UTXO financial flows and network telemetry</div>
            <div><span className="cmd-tag" onClick={() => onRunCommand('trace 12dhqUGwzF6c6eW5F7DkyXyqBmW1 1EcgU6KKS36aF55d65f5a')}>trace &lt;source&gt; &lt;target&gt;</span> - Run multi-hop shortest path velocity trace</div>
            <div><span className="cmd-tag" onClick={() => onRunCommand('taint 12dhqUGwzF6c6eW5F7DkyXyqBmW1')}>taint &lt;seed_address&gt;</span> - Trace forward dirty coin contamination decay</div>
            <div><span className="cmd-tag" onClick={() => onRunCommand('alerts')}>alerts</span> - View prioritized heuristic and ML typology alert candidates</div>
            <div><span className="cmd-tag" onClick={() => onRunCommand('dossier 58234917')}>dossier &lt;txid&gt;</span> - Generate court-admissible Section 91 Cr.P.C. legal dossier</div>
            <div><span className="cmd-tag" onClick={() => onRunCommand('tor')}>tor</span> - View global Tor network timing entropy and exit node profiler</div>
            <div><span className="cmd-tag" onClick={() => onRunCommand('status')}>status</span> - Check forensic memory store and clustering health</div>
            <div><span className="cmd-tag" onClick={() => onRunCommand('clear')}>clear</span> - Clear terminal buffer (Shortcut: Ctrl+L)</div>
          </div>
        </div>
      )}

      {/* 10. ERROR MESSAGE */}
      {entry.type === 'ERROR' && (
        <div className="output-block output-error" style={{ color: '#ff3344', padding: '4px 0' }}>
          {entry.content?.message || 'An error occurred.'}
        </div>
      )}

      {/* 11. SUCCESS MESSAGE */}
      {entry.type === 'SUCCESS' && (
        <div className="output-block output-success" style={{ color: '#33ff88', padding: '4px 0' }}>
          {entry.content?.message || 'Command completed successfully.'}
        </div>
      )}

      {/* 12. TEXT MESSAGE */}
      {entry.type === 'TEXT' && (
        <div className="output-block" style={{ color: 'var(--fg-white)', padding: '2px 0' }}>
          {entry.content?.message || ''}
        </div>
      )}
    </div>
  );
};
