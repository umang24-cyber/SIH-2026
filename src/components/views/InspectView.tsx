import React from 'react';
import { ForensicNode } from '../../types/terminal';

interface InspectViewProps {
  node: ForensicNode;
  data?: any;
  onRunCommand: (cmd: string) => void;
}

export const InspectView: React.FC<InspectViewProps> = ({ node, data, onRunCommand }) => {
  const getRiskBadge = (score: number) => {
    if (score >= 80) return <span className="badge badge-risk-high">CRITICAL THREAT ({score}/100)</span>;
    if (score >= 50) return <span className="badge badge-risk-med">ELEVATED RISK ({score}/100)</span>;
    return <span className="badge badge-risk-low">LOW RISK ({score}/100)</span>;
  };

  const isTx = node.type === 'TRANSACTION' || !!data?.txid;
  const isEntity = !isTx;

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', fontSize: '14px' }}>
      <div style={{ borderBottom: '1px solid #00ff66', paddingBottom: '6px', marginBottom: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
        <h2 style={{ fontSize: '18px', color: '#33ff88' }}>
          &gt; FORENSIC INSPECTOR :: {node.id}
        </h2>
        <div>{getRiskBadge(node.riskScore)}</div>
      </div>

      {/* Grid of metadata */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '12px', marginBottom: '16px' }}>
        <div style={{ border: '1px solid #007a33', padding: '10px', background: '#000c04' }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '6px', borderBottom: '1px dashed #004d20', paddingBottom: '4px' }}>
            ON-CHAIN IDENTITY &amp; CLUSTERING
          </div>
          <p><strong>TARGET IDENTIFIER:</strong> <span style={{ color: '#33ff88' }}>{node.id}</span></p>
          <p><strong>ENTITY TYPE:</strong> <span style={{ color: '#00ff66' }}>{node.type}</span></p>
          <p><strong>CIOH CLUSTER ID:</strong> <span style={{ color: '#33ff88' }}>{node.clusterId || 'UNCLUSTERED'}</span></p>
          {node.isLicitExchange !== undefined && (
            <p><strong>EXCHANGE STATUS:</strong> <span style={{ color: node.isLicitExchange ? '#33ff88' : '#ffaa33' }}>{node.isLicitExchange ? 'KNOWN LICIT EXCHANGE' : 'PRIVATE/SUSPECT WALLET'}</span></p>
          )}
        </div>

        <div style={{ border: '1px solid #007a33', padding: '10px', background: '#000c04' }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '6px', borderBottom: '1px dashed #004d20', paddingBottom: '4px' }}>
            LEDGER FINANCIAL METRICS
          </div>
          <p><strong>BALANCE / VOLUME:</strong> <span style={{ color: '#33ff88' }}>{(node.balanceBtc || node.balanceEth || 0).toLocaleString()} BTC</span></p>
          <p><strong>TX LIFETIME COUNT:</strong> {(node.txCount || 0).toLocaleString()} transactions</p>
          <p><strong>FIRST SEEN:</strong> {node.firstSeen || 'N/A'}</p>
          <p><strong>LAST OBSERVED:</strong> {node.lastSeen || 'N/A'}</p>
        </div>
      </div>

      {/* Network Telemetry Breakdown if Transaction */}
      {data?.network && (
        <div style={{ border: '1px solid #007a33', padding: '10px', background: '#000c04', marginBottom: '16px' }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '6px' }}>
            RECORDED P2P NETWORK TELEMETRY
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '8px' }}>
            <div><strong>OBSERVED RELAY IP:</strong> <code>{data.network.relay_ip || '0.0.0.0'}</code></div>
            <div><strong>RECORDED COUNTRY CODE:</strong> {data.network.country_code || 'US'}</div>
            <div><strong>ASN:</strong> {data.network.asn || 'Unknown'}</div>
            <div><strong>ISP:</strong> {data.network.isp || 'Unknown'}</div>
            <div><strong>NODE TYPE:</strong> <span style={{ color: data.network.node_type?.includes('tor') ? '#ff3344' : '#33ff88' }}>{data.network.node_type}</span></div>
            <div><strong>PROPAGATION Δt:</strong> {data.network.propagation_delta_ms} ms</div>
          </div>
        </div>
      )}

      {/* Multi-I/O UTXO Breakdown if Transaction */}
      {data?.input_addresses && (
        <div style={{ border: '1px solid #007a33', padding: '10px', background: '#000c04', marginBottom: '16px' }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '6px' }}>
            UTXO FINANCIAL DECOMPOSITION ({data.input_addresses.length} Inputs → {data.output_addresses?.length || 0} Outputs | Fee: {data.fee_btc} BTC)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <div style={{ color: '#33ff88', fontSize: '13px', marginBottom: '4px' }}>INPUTS:</div>
              {data.input_addresses.slice(0, 5).map((addr: string, idx: number) => (
                <div key={idx} style={{ fontSize: '12px', color: '#aaffaa' }}>
                  • <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${addr}`)}>{addr}</span>: {data.input_amounts?.[idx]} BTC
                </div>
              ))}
            </div>
            <div>
              <div style={{ color: '#33ff88', fontSize: '13px', marginBottom: '4px' }}>OUTPUTS:</div>
              {data.output_addresses?.slice(0, 5).map((addr: string, idx: number) => (
                <div key={idx} style={{ fontSize: '12px', color: '#aaffaa' }}>
                  • <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${addr}`)}>{addr}</span>: {data.output_amounts?.[idx]} BTC
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Quick Navigation Commands */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', fontSize: '14px', marginTop: '14px' }}>
        <span style={{ color: '#007a33' }}>Available Actions:</span>
        <span className="cmd-clickable" onClick={() => onRunCommand('graph')}>
          [Switch to 3D Graph]
        </span>
        {isEntity && (
          <span className="cmd-clickable" onClick={() => onRunCommand(`taint ${node.id}`)}>
            [Trace Taint from this Wallet]
          </span>
        )}
        {isTx && (
          <span className="cmd-clickable" onClick={() => onRunCommand(`dossier ${node.id}`)}>
            [Generate Investigation Summary]
          </span>
        )}
      </div>
    </div>
  );
};
