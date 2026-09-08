import React from 'react';

interface SearchViewProps {
  query: string;
  matchType: string;
  matches: any[];
  onRunCommand: (cmd: string) => void;
  onClose?: () => void;
}

export const SearchView: React.FC<SearchViewProps> = ({
  query,
  matchType,
  matches,
  onRunCommand,
  onClose,
}) => {
  const getBadgeColor = () => {
    switch (matchType) {
      case 'TRANSACTION':
        return '#38bdf8';
      case 'WALLET':
        return '#34d399';
      case 'SCENARIO':
        return '#fbbf24';
      case 'TELEMETRY':
        return '#c084fc';
      default:
        return '#94a3b8';
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', fontSize: '14px', fontFamily: 'monospace' }}>
      {/* Header */}
      <div
        style={{
          borderBottom: '1px solid #00ff66',
          paddingBottom: '8px',
          marginBottom: '14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '16px', color: '#33ff88', fontWeight: 'bold' }}>
            &gt; FORENSIC SEARCH RESULTS :: "{query}"
          </span>
          <span
            style={{
              padding: '2px 8px',
              borderRadius: '3px',
              fontSize: '11px',
              fontWeight: 'bold',
              border: `1px solid ${getBadgeColor()}`,
              color: getBadgeColor(),
              background: 'rgba(0,0,0,0.4)',
            }}
          >
            TYPE: {matchType} ({matches.length} MATCH{matches.length === 1 ? '' : 'ES'})
          </span>
        </div>
        {onClose && (
          <span className="cmd-tag" onClick={onClose} style={{ cursor: 'pointer' }}>
            [Close]
          </span>
        )}
      </div>

      {/* No Results */}
      {matches.length === 0 && (
        <div
          style={{
            border: '1px solid #ff4455',
            background: '#180003',
            padding: '16px',
            color: '#ff8899',
          }}
        >
          <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>
            NO MATCHES FOUND FOR: "{query}"
          </div>
          <div style={{ color: '#aaa', fontSize: '12px', lineHeight: '1.6' }}>
            Search Tips:
            <ul style={{ margin: '6px 0 0 16px', padding: 0 }}>
              <li><strong>TxID:</strong> Enter numeric integer (e.g. <span className="cmd-clickable" onClick={() => onRunCommand('search 881920041')}>search 881920041</span>)</li>
              <li><strong>Wallet Address:</strong> Enter full Bitcoin address (e.g. <span className="cmd-clickable" onClick={() => onRunCommand('search 1PeelHeadWallet0001')}>1PeelHeadWallet0001</span>)</li>
              <li><strong>Scenario ID:</strong> Prefix match (e.g. <span className="cmd-clickable" onClick={() => onRunCommand('search peeling_chain_04651')}>peeling_chain_04651</span>)</li>
              <li><strong>Network Telemetry:</strong> IP or ASN query (e.g. <span className="cmd-clickable" onClick={() => onRunCommand('search AS49981')}>AS49981</span> or <span className="cmd-clickable" onClick={() => onRunCommand('search 38.148')}>38.148</span>)</li>
            </ul>
          </div>
        </div>
      )}

      {/* Transaction Matches */}
      {matchType === 'TRANSACTION' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {matches.map((tx: any, idx: number) => (
            <div
              key={tx.txid || idx}
              style={{
                border: '1px solid #0284c7',
                background: '#031826',
                padding: '14px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '10px',
                  flexWrap: 'wrap',
                }}
              >
                <div>
                  <span style={{ color: '#38bdf8', fontWeight: 'bold', fontSize: '15px' }}>
                    TXID: {tx.txid}
                  </span>
                  <span style={{ color: '#94a3b8', fontSize: '12px', marginLeft: '12px' }}>
                    {tx.timestamp}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <span className="cmd-tag" onClick={() => onRunCommand(`inspect ${tx.txid}`)}>
                    [Inspect]
                  </span>
                  <span className="cmd-tag" onClick={() => onRunCommand(`flow ${tx.txid}`)}>
                    [Flow]
                  </span>
                  <span className="cmd-tag" onClick={() => onRunCommand(`dossier ${tx.txid}`)}>
                    [Dossier]
                  </span>
                </div>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '10px',
                  fontSize: '12px',
                  background: '#02101a',
                  padding: '10px',
                  border: '1px solid #03446a',
                }}
              >
                <div>
                  <div style={{ color: '#64748b' }}>TOTAL VOLUME</div>
                  <div style={{ color: '#38bdf8', fontWeight: 'bold' }}>
                    {tx.amount_btc || (Array.isArray(tx.input_amounts) ? tx.input_amounts.reduce((a: number, b: number) => a + b, 0).toFixed(6) : '0')} BTC
                  </div>
                </div>
                <div>
                  <div style={{ color: '#64748b' }}>MINER FEE</div>
                  <div style={{ color: '#cbd5e1' }}>{tx.fee_btc} BTC</div>
                </div>
                <div>
                  <div style={{ color: '#64748b' }}>SCRIPT TYPE</div>
                  <div style={{ color: '#cbd5e1' }}>{tx.script_type || 'P2PKH'}</div>
                </div>
                <div>
                  <div style={{ color: '#64748b' }}>RELAY IP / ASN</div>
                  <div style={{ color: '#cbd5e1' }}>
                    {tx.relay_ip || tx.network?.relay_ip} ({tx.asn || tx.network?.asn})
                  </div>
                </div>
                <div>
                  <div style={{ color: '#64748b' }}>NODE INFRASTRUCTURE</div>
                  <div style={{ color: tx.node_type === 'tor' ? '#f43f5e' : '#38bdf8' }}>
                    {(tx.node_type || tx.network?.node_type || 'residential').toUpperCase()}
                  </div>
                </div>
                <div>
                  <div style={{ color: '#64748b' }}>SCENARIO CLUSTER</div>
                  <span
                    className="cmd-clickable"
                    onClick={() => onRunCommand(`g ${tx.scenario_id}`)}
                  >
                    {tx.scenario_id || 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Wallet Matches */}
      {matchType === 'WALLET' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {matches.map((wallet: any, idx: number) => (
            <div
              key={wallet.address || idx}
              style={{
                border: '1px solid #059669',
                background: '#022116',
                padding: '14px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '10px',
                  flexWrap: 'wrap',
                }}
              >
                <div>
                  <span style={{ color: '#34d399', fontWeight: 'bold', fontSize: '15px' }}>
                    WALLET: {wallet.address}
                  </span>
                  {wallet.alias && (
                    <span style={{ color: '#a7f3d0', fontSize: '12px', marginLeft: '10px' }}>
                      ({wallet.alias})
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <span className="cmd-tag" onClick={() => onRunCommand(`inspect ${wallet.address}`)}>
                    [Inspect]
                  </span>
                  <span className="cmd-tag" onClick={() => onRunCommand(`taint ${wallet.address}`)}>
                    [Taint]
                  </span>
                </div>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: '10px',
                  fontSize: '12px',
                  background: '#01150e',
                  padding: '10px',
                  border: '1px solid #065f46',
                }}
              >
                <div>
                  <div style={{ color: '#6ee7b7' }}>BALANCE</div>
                  <div style={{ color: '#fff', fontWeight: 'bold' }}>
                    {wallet.balance_btc !== undefined ? wallet.balance_btc : (wallet.balance || 0)} BTC
                  </div>
                </div>
                <div>
                  <div style={{ color: '#6ee7b7' }}>TRANSACTIONS</div>
                  <div style={{ color: '#fff' }}>{wallet.tx_count || 0} TXs</div>
                </div>
                <div>
                  <div style={{ color: '#6ee7b7' }}>RISK SCORE</div>
                  <div style={{ color: (wallet.risk_score || 0) > 60 ? '#f43f5e' : '#34d399', fontWeight: 'bold' }}>
                    {wallet.risk_score || 0} / 100
                  </div>
                </div>
                <div>
                  <div style={{ color: '#6ee7b7' }}>CIOH CLUSTER</div>
                  <div style={{ color: '#cbd5e1' }}>{wallet.cluster_id || 'entity_unassigned'}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Scenario Matches */}
      {matchType === 'SCENARIO' && (
        <div style={{ border: '1px solid #d97706', background: '#1c1303', padding: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <div style={{ color: '#fbbf24', fontWeight: 'bold', fontSize: '15px' }}>
              SCENARIO CLUSTER MEMBERS ({matches.length} SAMPLE TRANSACTIONS)
            </div>
            <div style={{ display: 'flex', gap: '6px' }}>
              <span className="cmd-tag" onClick={() => onRunCommand(`g ${query}`)}>
                [Open 3D Graph]
              </span>
              <span className="cmd-tag" onClick={() => onRunCommand(`communities ${query}`)}>
                [Communities]
              </span>
              <span className="cmd-tag" onClick={() => onRunCommand(`anomaly ${query}`)}>
                [Score Anomaly]
              </span>
            </div>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #d97706', textAlign: 'left', color: '#fbbf24' }}>
                <th style={{ padding: '6px' }}>TxID</th>
                <th style={{ padding: '6px' }}>Timestamp</th>
                <th style={{ padding: '6px' }}>Volume (BTC)</th>
                <th style={{ padding: '6px' }}>Relay IP</th>
                <th style={{ padding: '6px' }}>Node Type</th>
                <th style={{ padding: '6px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {matches.map((tx: any) => {
                const totalIn = Array.isArray(tx.input_amounts) ? tx.input_amounts.reduce((a: number, b: number) => a + b, 0).toFixed(6) : (tx.amount_btc || '0');
                return (
                  <tr key={tx.txid} style={{ borderBottom: '1px solid #332002' }}>
                    <td style={{ padding: '6px', color: '#fbbf24', fontWeight: 'bold' }}>
                      <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${tx.txid}`)}>
                        {tx.txid}
                      </span>
                    </td>
                    <td style={{ padding: '6px', color: '#94a3b8' }}>{tx.timestamp}</td>
                    <td style={{ padding: '6px', color: '#fff' }}>{totalIn}</td>
                    <td style={{ padding: '6px', color: '#cbd5e1' }}>{tx.network?.relay_ip || tx.relay_ip || 'N/A'}</td>
                    <td style={{ padding: '6px' }}>
                      <span style={{ color: (tx.network?.node_type || tx.node_type) === 'tor' ? '#f43f5e' : '#fbbf24' }}>
                        {tx.network?.node_type || tx.node_type || 'relay'}
                      </span>
                    </td>
                    <td style={{ padding: '6px' }}>
                      <span className="cmd-tag" onClick={() => onRunCommand(`flow ${tx.txid}`)}>
                        [Flow]
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Telemetry Matches (IP or ASN) */}
      {matchType === 'TELEMETRY' && (
        <div style={{ border: '1px solid #7c3aed', background: '#130826', padding: '14px' }}>
          <div style={{ color: '#c084fc', fontWeight: 'bold', fontSize: '15px', marginBottom: '10px' }}>
            INFRASTRUCTURE RELAY ACTIVITY ({matches.length} OBSERVED TRANSACTIONS)
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #7c3aed', textAlign: 'left', color: '#c084fc' }}>
                <th style={{ padding: '6px' }}>TxID</th>
                <th style={{ padding: '6px' }}>Relay IP</th>
                <th style={{ padding: '6px' }}>ASN</th>
                <th style={{ padding: '6px' }}>Node Type</th>
                <th style={{ padding: '6px' }}>Scenario</th>
                <th style={{ padding: '6px' }}>Latency Δt</th>
                <th style={{ padding: '6px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {matches.map((tx: any) => {
                const relayIp = tx.network?.relay_ip || tx.relay_ip || 'N/A';
                const asn = tx.network?.asn || tx.asn || 'N/A';
                const nodeType = tx.network?.node_type || tx.node_type || 'standard';
                const propDelta = tx.network?.propagation_delta_ms ?? tx.propagation_delta_ms;
                return (
                  <tr key={tx.txid} style={{ borderBottom: '1px solid #281045' }}>
                    <td style={{ padding: '6px', color: '#c084fc', fontWeight: 'bold' }}>
                      <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${tx.txid}`)}>
                        {tx.txid}
                      </span>
                    </td>
                    <td style={{ padding: '6px', color: '#cbd5e1' }}>{relayIp}</td>
                    <td style={{ padding: '6px', color: '#e9d5ff' }}>{asn}</td>
                    <td style={{ padding: '6px' }}>
                      <span style={{ color: nodeType.includes('tor') ? '#f43f5e' : '#38bdf8' }}>
                        {nodeType}
                      </span>
                    </td>
                    <td style={{ padding: '6px' }}>
                      <span className="cmd-clickable" onClick={() => onRunCommand(`graph ${tx.scenario_id}`)}>
                        {tx.scenario_id}
                      </span>
                    </td>
                    <td style={{ padding: '6px', color: '#cbd5e1' }}>
                      {propDelta !== undefined ? `${propDelta} ms` : 'N/A'}
                    </td>
                    <td style={{ padding: '6px' }}>
                      <span className="cmd-tag" onClick={() => onRunCommand(`flow ${tx.txid}`)}>
                        [Flow]
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
