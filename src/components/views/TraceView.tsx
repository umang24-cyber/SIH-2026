import React from 'react';
import { ForensicNode, ForensicLink } from '../../types/terminal';

interface TraceViewProps {
  sourceId: string;
  targetId: string;
  nodes: ForensicNode[];
  links: ForensicLink[];
  onRunCommand: (cmd: string) => void;
}

export const TraceView: React.FC<TraceViewProps> = ({
  sourceId,
  targetId,
  nodes,
  links,
  onRunCommand
}) => {
  // Simple BFS / Dijkstra shortest path finder between sourceId and targetId
  const findPath = (src: string, dst: string) => {
    const queue: { current: string; path: string[]; edgePath: ForensicLink[] }[] = [
      { current: src, path: [src], edgePath: [] }
    ];
    const visited = new Set<string>([src]);

    while (queue.length > 0) {
      const { current, path, edgePath } = queue.shift()!;
      if (current.toLowerCase() === dst.toLowerCase()) {
        return { path, edgePath };
      }

      // Check outgoing links
      const outgoing = links.filter(l => l.source.toLowerCase() === current.toLowerCase());
      for (const edge of outgoing) {
        if (!visited.has(edge.target)) {
          visited.add(edge.target);
          queue.push({
            current: edge.target,
            path: [...path, edge.target],
            edgePath: [...edgePath, edge]
          });
        }
      }
    }
    return null;
  };

  const pathResult = findPath(sourceId, targetId);

  const getNodeInfo = (id: string) => nodes.find(n => n.id.toLowerCase() === id.toLowerCase());

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', fontSize: '15px' }}>
      <div style={{ borderBottom: '1px solid #00ff66', paddingBottom: '6px', marginBottom: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
        <h2 style={{ fontSize: '18px', color: '#33ff88' }}>
          &gt; MULTI-HOP FUND ROUTE TRACER :: {sourceId} ===&gt; {targetId}
        </h2>
        <span className="badge badge-risk-high">GRAPH TRAVERSAL COMPLETED</span>
      </div>

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
        </div>
      )}
    </div>
  );
};
