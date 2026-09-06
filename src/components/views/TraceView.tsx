import React from 'react';
import { ForensicNode, ForensicLink } from '../../types/terminal';
import { TraceResponse } from '../../services/api';

interface TraceViewProps {
  sourceId: string;
  targetId: string;
  nodes?: ForensicNode[];
  links?: ForensicLink[];
  traceResult?: TraceResponse | null;
  onRunCommand: (cmd: string) => void;
}

export const TraceView: React.FC<TraceViewProps> = ({
  sourceId,
  targetId,
  nodes = [],
  links = [],
  traceResult,
  onRunCommand
}) => {
  const hops = traceResult?.hops || [];

  // If backend traceResult is provided and path found
  if (traceResult && traceResult.path_found && hops.length > 0) {
    return (
      <div style={{ maxWidth: '1100px', margin: '0 auto', fontSize: '15px' }}>
        <div style={{ borderBottom: '1px solid #00ff66', paddingBottom: '6px', marginBottom: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
          <h2 style={{ fontSize: '18px', color: '#33ff88' }}>
            &gt; MULTI-HOP BITCOIN FLOW TRACER :: {sourceId} ===&gt; {targetId}
          </h2>
          <span className="badge badge-risk-high" style={{ background: '#003311', color: '#33ff88', border: '1px solid #00ff66', padding: '4px 8px', borderRadius: '3px' }}>
            BFS TRAVERSAL ({traceResult.hop_count} HOPS | {traceResult.total_transferred_btc} BTC)
          </span>
        </div>

        <div style={{ border: '1px solid #007a33', padding: '12px', background: '#000c04', marginBottom: '16px' }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '8px' }}>
            FORWARD LAUNDERING VELOCITY PIPELINE ({hops.length} HOPS LINKED)
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {hops.map((hop, idx) => (
              <div key={`${hop.txid}-${idx}`}>
                <div style={{ border: '1px solid #004d20', padding: '8px', background: '#001406', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
                  <div>
                    <span style={{ color: '#33ff88', fontWeight: 'bold' }}>[HOP {hop.hop_index}]</span>&nbsp;
                    <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${hop.from_wallet}`)}>
                      {hop.from_wallet}
                    </span>
                    <span style={{ color: '#00ff66' }}> ➔ </span>
                    <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${hop.to_wallet}`)}>
                      {hop.to_wallet}
                    </span>
                  </div>
                </div>

                <div style={{ padding: '6px 0 6px 24px', borderLeft: '2px dashed #00ff66', marginLeft: '16px', color: '#33ff88', fontSize: '13px' }}>
                  <div>
                    ▼ <strong>TRANSFERRED:</strong> {hop.amount_btc} BTC | <strong>TXID:</strong> <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${hop.txid}`)}>{hop.txid}</span>
                    {hop.flagged_typology && <span style={{ color: '#ff3344', marginLeft: '10px' }}>⚠️ [{hop.flagged_typology.toUpperCase()}]</span>}
                  </div>
                  <div style={{ color: '#007a33' }}>TIMESTAMP: {hop.timestamp}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <span className="cmd-clickable" onClick={() => onRunCommand('graph')}>
            [Open Graph Visualizer]
          </span>
          <span className="cmd-clickable" onClick={() => onRunCommand(`taint ${sourceId}`)}>
            [Analyze Taint Decay]
          </span>
        </div>
      </div>
    );
  }

  // Fallback if path not found
  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', fontSize: '15px' }}>
      <div style={{ borderBottom: '1px solid #00ff66', paddingBottom: '6px', marginBottom: '14px' }}>
        <h2 style={{ fontSize: '18px', color: '#33ff88' }}>
          &gt; MULTI-HOP BITCOIN FLOW TRACER :: {sourceId} ===&gt; {targetId}
        </h2>
      </div>
<<<<<<< HEAD
      <div style={{ border: '1px solid #ff3344', padding: '16px', background: '#1a0003' }}>
        <div style={{ color: '#ff3344', fontWeight: 'bold', marginBottom: '8px' }}>
          [!] NO DIRECT PATH FOUND BETWEEN {sourceId} AND {targetId}
        </div>
        <p style={{ color: '#ff8888', marginBottom: '10px' }}>
          The forensic engine could not locate an active transaction sequence between these two addresses within 5 hops.
        </p>
        <div style={{ color: '#00ff66' }}>
          Tip: Inspect the source wallet directly or check taint propagation:<br />
          &gt; <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${sourceId}`)}>inspect {sourceId}</span><br />
          &gt; <span className="cmd-clickable" onClick={() => onRunCommand(`taint ${sourceId}`)}>taint {sourceId}</span>
=======

      {pathResult ? (
        <div>
          <div style={{ border: '1px solid #007a33', padding: '12px', background: '#000c04', marginBottom: '16px' }}>
            <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '8px' }}>
              DETECTED LAUNDERING VELOCITY PIPELINE ({pathResult.path.length} HOPS)
            </div>
            
            {/* Visual Hop Flow */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {pathResult.path.map((nodeId, idx) => {
                const node = getNodeInfo(nodeId);
                const nextEdge = pathResult.edgePath[idx];

                return (
                  <div key={nodeId}>
                    <div style={{ border: '1px solid #004d20', padding: '8px', background: '#001406', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
                      <div>
                        <span style={{ color: '#33ff88', fontWeight: 'bold' }}>[HOP {idx + 1}]</span>&nbsp;
                        <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${nodeId}`)}>
                          {nodeId}
                        </span>
                        <span style={{ color: '#007a33' }}> ({node?.label || 'UNLABELED'})</span>
                      </div>
                      <div>
                        <span style={{ color: node && node.riskScore > 75 ? '#ff3344' : '#00ff66' }}>
                          RISK: {node?.riskScore || 50}/100
                        </span>
                        <span style={{ marginLeft: '12px', color: '#33ff88' }}>
                          BAL: {node?.balanceBtc ?? node?.balanceEth ?? 0} BTC
                        </span>
                      </div>
                    </div>

                    {nextEdge && (
                      <div style={{ padding: '6px 0 6px 24px', borderLeft: '2px dashed #00ff66', marginLeft: '16px', color: '#33ff88', fontSize: '13px' }}>
                        <div>▼ <strong>TRANSFERRED:</strong> {nextEdge.amountBtc ?? nextEdge.amountEth} BTC | <strong>TX:</strong> {nextEdge.txHash}</div>
                        <div style={{ color: '#007a33' }}>TIMESTAMP: {nextEdge.timestamp}</div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <span className="cmd-clickable" onClick={() => onRunCommand('graph')}>
              [Inspect Path in 3D WebGL Graph]
            </span>
            <span className="cmd-clickable" onClick={() => onRunCommand('dmesg')}>
              [View Kernel Logs]
            </span>
            <span className="cmd-clickable" onClick={() => onRunCommand('home')}>
              [Return Home]
            </span>
          </div>
        </div>
      ) : (
        <div style={{ border: '1px solid #ff3344', padding: '16px', background: '#1a0003' }}>
          <div style={{ color: '#ff3344', fontWeight: 'bold', marginBottom: '8px' }}>
            [!] NO DIRECT DIRECTED PATH FOUND BETWEEN {sourceId} AND {targetId}
          </div>
          <p style={{ color: '#ff8888', marginBottom: '10px' }}>
            The graph engine could not find an unbroken directed flow sequence between these two addresses with current depth parameters.
          </p>
          <div style={{ color: '#00ff66' }}>
            Try tracing known verified candidate typologies: <br />
            &gt; <span className="cmd-clickable" onClick={() => onRunCommand('trace peel_0564')}>trace peel_0564</span> (4-Hop UTXO Peeling Chain)<br />
            &gt; <span className="cmd-clickable" onClick={() => onRunCommand('trace layer_1054')}>trace layer_1054</span> (14-Branch Reconvergence Layering)<br />
            &gt; <span className="cmd-clickable" onClick={() => onRunCommand('trace 1PTqbgVoXSbuzQKrDGw2M2tchx 1s6D1TaSbKqeTG5YMhWWRJ85Ve8s7Y')}>trace 1PTqbgVoXSbuzQKrDGw2M2tchx 1s6D1TaSbKqeTG5YMhWWRJ85Ve8s7Y</span>
          </div>
>>>>>>> origin/graph
        </div>
      </div>
    </div>
  );
};
