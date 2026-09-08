import React from 'react';

interface TelemetryStatsData {
  total_transactions: number;
  total_unique_wallets: number;
  total_scenarios: number;
  node_type_distribution: Record<string, number>;
  top_asns: Record<string, number>;
  top_countries: Record<string, number>;
  script_type_distribution: Record<string, number>;
  average_propagation_latency_ms: Record<string, number>;
}

interface TelemetryStatsViewProps {
  stats: TelemetryStatsData;
  onRunCommand: (cmd: string) => void;
  onClose?: () => void;
}

export const TelemetryStatsView: React.FC<TelemetryStatsViewProps> = ({
  stats,
  onRunCommand,
  onClose,
}) => {
  const totalTx = stats.total_transactions || 1;

  const getNodeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'tor':
        return '#f43f5e';
      case 'vpn':
        return '#f59e0b';
      case 'datacenter':
        return '#38bdf8';
      case 'bulletproof':
        return '#e11d48';
      default:
        return '#10b981';
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', fontSize: '13px', fontFamily: 'monospace' }}>
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
        <div>
          <span style={{ fontSize: '16px', color: '#33ff88', fontWeight: 'bold' }}>
            &gt; GLOBAL P2P BROADCAST & TELEMETRY STATISTICS
          </span>
          <span style={{ color: '#94a3b8', fontSize: '12px', marginLeft: '10px' }}>
            ({totalTx.toLocaleString()} TRANSACTIONS PROFILED)
          </span>
        </div>
        {onClose && (
          <span className="cmd-tag" onClick={onClose} style={{ cursor: 'pointer' }}>
            [Close]
          </span>
        )}
      </div>

      {/* Top Level Counts */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '12px',
          marginBottom: '16px',
        }}
      >
        <div style={{ border: '1px solid #00aa44', background: '#011508', padding: '12px' }}>
          <div style={{ color: '#77aa88', fontSize: '11px' }}>INDEXED TRANSACTIONS</div>
          <div style={{ color: '#33ff88', fontSize: '20px', fontWeight: 'bold', marginTop: '2px' }}>
            {stats.total_transactions.toLocaleString()}
          </div>
        </div>

        <div style={{ border: '1px solid #0284c7', background: '#021626', padding: '12px' }}>
          <div style={{ color: '#7dd3fc', fontSize: '11px' }}>UNIQUE WALLET NODES</div>
          <div style={{ color: '#38bdf8', fontSize: '20px', fontWeight: 'bold', marginTop: '2px' }}>
            {stats.total_unique_wallets.toLocaleString()}
          </div>
        </div>

        <div style={{ border: '1px solid #eab308', background: '#1c1503', padding: '12px' }}>
          <div style={{ color: '#fde047', fontSize: '11px' }}>SCENARIO CLUSTERS</div>
          <div style={{ color: '#fbbf24', fontSize: '20px', fontWeight: 'bold', marginTop: '2px' }}>
            {stats.total_scenarios.toLocaleString()}
          </div>
        </div>
      </div>

      {/* Node Type Distribution & Propagation Latency */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
          gap: '14px',
          marginBottom: '16px',
        }}
      >
        {/* Node Distribution */}
        <div style={{ border: '1px solid #00aa44', background: '#020d06', padding: '12px' }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', fontSize: '13px', marginBottom: '10px' }}>
            RELAY NODE TYPE DISTRIBUTION
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {Object.entries(stats.node_type_distribution || {}).map(([type, count]) => {
              const pct = ((count / totalTx) * 100).toFixed(1);
              const color = getNodeColor(type);
              return (
                <div key={type}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '2px' }}>
                    <span style={{ color, fontWeight: 'bold' }}>{type.toUpperCase()}</span>
                    <span style={{ color: '#94a3b8' }}>
                      {count.toLocaleString()} ({pct}%)
                    </span>
                  </div>
                  <div style={{ height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${pct}%`, height: '100%', background: color }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Latency by Node Type */}
        <div style={{ border: '1px solid #0284c7', background: '#02101a', padding: '12px' }}>
          <div style={{ color: '#38bdf8', fontWeight: 'bold', fontSize: '13px', marginBottom: '10px' }}>
            AVERAGE PROPAGATION LATENCY Δt (ms)
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {Object.entries(stats.average_propagation_latency_ms || {}).map(([type, lat]) => {
              const color = getNodeColor(type);
              const maxLat = 5000;
              const barWidth = Math.min(100, Math.max(5, (lat / maxLat) * 100));
              return (
                <div key={type}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '2px' }}>
                    <span style={{ color, fontWeight: 'bold' }}>{type.toUpperCase()}</span>
                    <span style={{ color: '#fff' }}>
                      {lat.toFixed(1)} ms
                    </span>
                  </div>
                  <div style={{ height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${barWidth}%`, height: '100%', background: color }} />
                  </div>
                </div>
              );
            })}
          </div>
          <div style={{ color: '#64748b', fontSize: '11px', marginTop: '10px' }}>
            * Tor relays exhibit significantly higher broadcast latency due to multi-hop onion routing.
          </div>
        </div>
      </div>

      {/* Top ASNs, Countries, and Script Types */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '14px',
        }}
      >
        {/* Top ASNs */}
        <div style={{ border: '1px solid #7c3aed', background: '#100624', padding: '12px' }}>
          <div style={{ color: '#c084fc', fontWeight: 'bold', fontSize: '13px', marginBottom: '8px' }}>
            TOP AUTONOMOUS SYSTEMS (ASNs)
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            {Object.entries(stats.top_asns || {}).slice(0, 8).map(([asn, count]) => (
              <div
                key={asn}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '12px',
                  padding: '3px 0',
                  borderBottom: '1px solid #200d45',
                }}
              >
                <span
                  className="cmd-clickable"
                  onClick={() => onRunCommand(`search ${asn}`)}
                  style={{ color: '#c084fc' }}
                >
                  {asn}
                </span>
                <span style={{ color: '#e9d5ff' }}>{count.toLocaleString()} TXs</span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Countries */}
        <div style={{ border: '1px solid #d97706', background: '#1c1303', padding: '12px' }}>
          <div style={{ color: '#fbbf24', fontWeight: 'bold', fontSize: '13px', marginBottom: '8px' }}>
            TOP ORIGIN JURISDICTIONS
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            {Object.entries(stats.top_countries || {}).slice(0, 8).map(([country, count]) => (
              <div
                key={country}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '12px',
                  padding: '3px 0',
                  borderBottom: '1px solid #332002',
                }}
              >
                <span style={{ color: '#fbbf24', fontWeight: 'bold' }}>{country}</span>
                <span style={{ color: '#fde68a' }}>{count.toLocaleString()} TXs</span>
              </div>
            ))}
          </div>
        </div>

        {/* Script Types */}
        <div style={{ border: '1px solid #059669', background: '#021c13', padding: '12px' }}>
          <div style={{ color: '#34d399', fontWeight: 'bold', fontSize: '13px', marginBottom: '8px' }}>
            SCRIPT TYPE DISTRIBUTION
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            {Object.entries(stats.script_type_distribution || {}).map(([script, count]) => (
              <div
                key={script}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '12px',
                  padding: '3px 0',
                  borderBottom: '1px solid #064e3b',
                }}
              >
                <span style={{ color: '#34d399', fontWeight: 'bold' }}>{script}</span>
                <span style={{ color: '#a7f3d0' }}>{count.toLocaleString()} TXs</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
