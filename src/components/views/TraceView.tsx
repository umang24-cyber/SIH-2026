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
        </div>
      </div>
    </div>
  );
};
