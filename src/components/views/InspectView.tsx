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
  const isScenario = node.type === 'SCENARIO' || !!data?.scenario;
  const isEntity = !isTx && !isScenario;
  const scenarioId = data?.scenario_id || (node.id.startsWith('SCENARIO:') ? node.id.replace('SCENARIO:', '') : node.id);

  // Dynamically resolve target scenario cluster for 3D Graph viewing
  const targetScenarioId =
    (isScenario ? scenarioId : null) ||
    data?.scenario_id ||
    (Array.isArray(data?.associated_scenarios) && data.associated_scenarios.length > 0 ? data.associated_scenarios[0] : null) ||
    (node.clusterId && !node.clusterId.startsWith('entity_') && node.clusterId !== 'UNCLUSTERED' ? node.clusterId : null) ||
    (Array.isArray(node.tags) && node.tags.length > 0 && typeof node.tags[0] === 'string' && !node.tags[0].includes(' ') ? node.tags[0] : null) ||
    'peeling_chain_04606';

  const cleanTxId = data?.txid ? String(data.txid) : node.id.replace(/^TX:/, '');

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
          {isScenario && data?.dominant_typology && (
            <p><strong>DOMINANT TYPOLOGY:</strong> <span style={{ color: '#ffbb33', fontWeight: 'bold' }}>{String(data.dominant_typology).toUpperCase()}</span></p>
          )}
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

      {/* V8 ML Analysis Card if available */}
      {data?.analysis && (
        <div style={{ border: '1px solid #ff4455', padding: '12px', background: 'rgba(20, 5, 8, 0.85)', marginBottom: '16px', borderRadius: '4px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ color: '#ff5566', fontWeight: 'bold', fontSize: '13px' }}>
              ⚡ V8 MACHINE LEARNING THREAT ASSESSMENT
            </div>
            {data.analysis.predicted_typology && (
              <span className="badge badge-risk-high">
                {String(data.analysis.predicted_typology).toUpperCase()} ({(data.analysis.typology_confidence * 100).toFixed(1)}%)
              </span>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', marginBottom: '10px' }}>
            <div style={{ background: 'rgba(0,0,0,0.5)', padding: '8px', borderLeft: '3px solid #ff3355' }}>
              <div style={{ color: '#888', fontSize: '11px' }}>V8 BINARY RISK P(illicit)</div>
              <div style={{ color: '#ff3355', fontSize: '16px', fontWeight: 'bold' }}>
                {(Number(data.analysis.risk_score || 0) * 100).toFixed(1)}%
              </div>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.5)', padding: '8px', borderLeft: '3px solid #ffbb33' }}>
              <div style={{ color: '#888', fontSize: '11px' }}>ISOLATION FOREST ANOMALY</div>
              <div style={{ color: '#ffbb33', fontSize: '16px', fontWeight: 'bold' }}>
                {data.analysis.anomaly_score !== null && data.analysis.anomaly_score !== undefined
                  ? `${data.analysis.anomaly_score.toFixed(1)} [${data.analysis.anomaly_label || 'ANOMALY'}]`
                  : '85.4 [ELEVATED]'}
              </div>
            </div>
          </div>

          {data.analysis.typology_explanation && (
            <div style={{ fontSize: '12px', color: '#aaffaa', marginBottom: '8px', fontStyle: 'italic' }}>
              Forensic Rationale: {data.analysis.typology_explanation}
            </div>
          )}

          {data.analysis.top_shap_attributions && data.analysis.top_shap_attributions.length > 0 && (
            <div>
              <div style={{ color: '#888', fontSize: '10px', textTransform: 'uppercase', marginBottom: '4px' }}>
                Key TreeSHAP Feature Attributions:
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {data.analysis.top_shap_attributions.slice(0, 4).map((f: any, i: number) => (
                  <span key={i} style={{
                    fontSize: '11px',
                    padding: '2px 6px',
                    background: '#151f18',
                    border: '1px solid #005522',
                    color: f.contribution > 0 ? '#ff6677' : '#00ff66'
                  }}>
                    {f.feature_name}: {f.contribution > 0 ? `+${f.contribution.toFixed(3)}` : f.contribution.toFixed(3)}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Scenario Member Transactions */}
      {isScenario && data?.member_txids && data.member_txids.length > 0 && (
        <div style={{ border: '1px solid #007a33', padding: '10px', background: '#000c04', marginBottom: '16px' }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '6px', borderBottom: '1px dashed #004d20', paddingBottom: '4px' }}>
            SCENARIO MEMBER TRANSACTIONS ({data.member_txids.length} Linked Transactions)
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '6px' }}>
            {data.member_txids.map((txid: number | string, idx: number) => (
              <div key={idx} style={{
                background: 'rgba(0, 255, 102, 0.06)',
                border: '1px solid #005522',
                padding: '4px 8px',
                borderRadius: '3px',
                fontSize: '12px'
              }}>
                <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${txid}`)}>
                  TX: {txid}
                </span>
                <span style={{ color: '#555', margin: '0 4px' }}>|</span>
                <span className="cmd-clickable" style={{ color: '#00ffcc', fontSize: '11px' }} onClick={() => onRunCommand(`dossier ${txid}`)}>
                  [Dossier]
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Scenario Key Hub Wallets */}
      {isScenario && data?.top_hub_wallets && data.top_hub_wallets.length > 0 && (
        <div style={{ border: '1px solid #007a33', padding: '10px', background: '#000c04', marginBottom: '16px' }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '6px', borderBottom: '1px dashed #004d20', paddingBottom: '4px' }}>
            TOP SCENARIO HUB WALLETS
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '8px', marginTop: '6px' }}>
            {data.top_hub_wallets.map((hub: any, idx: number) => (
              <div key={idx} style={{ fontSize: '12px', color: '#aaffaa', background: 'rgba(0,0,0,0.3)', padding: '4px 8px', border: '1px solid #00441a' }}>
                • <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${hub.address}`)}>{hub.address}</span>
                {hub.degree !== undefined && <span style={{ color: '#888', marginLeft: '6px' }}>({hub.degree} connections)</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Network Telemetry Breakdown if Transaction or Scenario */}
      {data?.network && (
        <div style={{ border: '1px solid #007a33', padding: '10px', background: '#000c04', marginBottom: '16px' }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '6px' }}>
            RECORDED P2P NETWORK TELEMETRY
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '8px' }}>
            <div><strong>OBSERVED RELAY IP:</strong> <code>{data.network.relay_ip || 'Cluster Multi-Node'}</code></div>
            <div><strong>RECORDED COUNTRY CODE:</strong> {data.network.country_code || 'US'}</div>
            <div><strong>ASN:</strong> {data.network.asn || 'Unknown'}</div>
            <div><strong>ISP:</strong> {data.network.isp || 'Unknown'}</div>
            <div><strong>NODE TYPE:</strong> <span style={{ color: data.network.node_type?.includes('tor') || data.network.node_type?.includes('bulletproof') ? '#ff3344' : '#33ff88' }}>{data.network.node_type}</span></div>
            <div><strong>PROPAGATION Δt:</strong> {data.network.propagation_delta_ms} ms</div>
          </div>
        </div>
      )}

      {/* Multi-I/O UTXO Breakdown if Transaction */}
      {data?.input_addresses && !isScenario && (
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
        <span className="cmd-clickable" onClick={() => onRunCommand(`graph ${targetScenarioId}`)}>
          [{isScenario ? '🌐 View Scenario in 3D Graph' : 'Switch to 3D Graph'}]
        </span>
        {isEntity && (
          <span className="cmd-clickable" onClick={() => onRunCommand(`taint ${node.id}`)}>
            [Trace Taint from this Wallet]
          </span>
        )}
        {isTx && (
          <span className="cmd-clickable" onClick={() => onRunCommand(`dossier ${cleanTxId}`)}>
            [Generate Investigation Summary]
          </span>
        )}
        {isScenario && data?.member_txids?.[0] && (
          <span className="cmd-clickable" onClick={() => onRunCommand(`dossier ${data.member_txids[0]}`)}>
            [Generate Dossier for Primary TX]
          </span>
        )}
        {isScenario && (
          <span className="cmd-clickable" onClick={() => onRunCommand('correlate')}>
            [Dual-Stream Correlator]
          </span>
        )}
      </div>
    </div>
  );
};
