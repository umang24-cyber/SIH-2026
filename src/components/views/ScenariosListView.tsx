import React from 'react';

interface ScenarioItem {
  scenario_id: string;
  transaction_count: number;
  total_volume_btc: number;
  primary_node_type: string;
}

interface ScenariosListViewProps {
  scenarios: ScenarioItem[];
  totalScenarios: number;
  currentPage: number;
  pageSize: number;
  currentPrefix?: string;
  onRunCommand: (cmd: string) => void;
  onClose?: () => void;
}

export const ScenariosListView: React.FC<ScenariosListViewProps> = ({
  scenarios,
  totalScenarios,
  currentPage,
  pageSize,
  currentPrefix = '',
  onRunCommand,
  onClose,
}) => {
  const totalPages = Math.max(1, Math.ceil(totalScenarios / pageSize));

  const filterTabs = [
    { label: 'ALL CLUSTERS', prefix: '' },
    { label: 'PEELING CHAINS', prefix: 'peel' },
    { label: 'MIXING / COINJOIN', prefix: 'mix' },
    { label: 'LAYERING', prefix: 'layer' },
    { label: 'RANSOMWARE', prefix: 'ransom' },
    { label: 'LICIT / NORMAL', prefix: 'licit' },
  ];

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
          marginBottom: '12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <div>
          <span style={{ fontSize: '16px', color: '#33ff88', fontWeight: 'bold' }}>
            &gt; SCENARIO CLUSTER DIRECTORY
          </span>
          <span style={{ color: '#94a3b8', fontSize: '12px', marginLeft: '10px' }}>
            ({totalScenarios.toLocaleString()} CLUSTERS INDEXED // PAGE {currentPage} OF {totalPages})
          </span>
        </div>
        {onClose && (
          <span className="cmd-tag" onClick={onClose} style={{ cursor: 'pointer' }}>
            [Close]
          </span>
        )}
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '6px', marginBottom: '14px', flexWrap: 'wrap' }}>
        {filterTabs.map((tab) => {
          const isActive = currentPrefix === tab.prefix;
          return (
            <button
              key={tab.label}
              onClick={() => onRunCommand(tab.prefix ? `scenarios ${tab.prefix} 1` : 'scenarios')}
              style={{
                background: isActive ? '#003816' : '#031008',
                border: `1px solid ${isActive ? '#00ff66' : '#005522'}`,
                color: isActive ? '#00ff66' : '#77aa88',
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 'bold',
                cursor: 'pointer',
                fontFamily: 'monospace',
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Scenarios Table */}
      <div style={{ border: '1px solid #00aa44', background: '#020d06', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #00ff66', background: '#00240e', color: '#33ff88' }}>
              <th style={{ padding: '8px 10px' }}>SCENARIO IDENTIFIER</th>
              <th style={{ padding: '8px 10px' }}>TX COUNT</th>
              <th style={{ padding: '8px 10px' }}>TOTAL VOLUME (BTC)</th>
              <th style={{ padding: '8px 10px' }}>PRIMARY RELAY INFRASTRUCTURE</th>
              <th style={{ padding: '8px 10px', textAlign: 'right' }}>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {scenarios.map((sc) => (
              <tr
                key={sc.scenario_id}
                style={{
                  borderBottom: '1px solid #002e12',
                  transition: 'background 0.15s',
                }}
              >
                <td style={{ padding: '8px 10px', fontWeight: 'bold', color: '#33ff88' }}>
                  <span
                    className="cmd-clickable"
                    onClick={() => onRunCommand(`graph ${sc.scenario_id}`)}
                  >
                    {sc.scenario_id}
                  </span>
                </td>
                <td style={{ padding: '8px 10px', color: '#e2e8f0' }}>
                  {sc.transaction_count.toLocaleString()}
                </td>
                <td style={{ padding: '8px 10px', color: '#fbbf24', fontWeight: 'bold' }}>
                  {sc.total_volume_btc.toFixed(4)} BTC
                </td>
                <td style={{ padding: '8px 10px' }}>
                  <span
                    style={{
                      border: `1px solid ${getNodeColor(sc.primary_node_type)}`,
                      color: getNodeColor(sc.primary_node_type),
                      padding: '2px 6px',
                      borderRadius: '3px',
                      fontSize: '10px',
                      fontWeight: 'bold',
                      background: 'rgba(0,0,0,0.3)',
                    }}
                  >
                    {sc.primary_node_type.toUpperCase()}
                  </span>
                </td>
                <td style={{ padding: '8px 10px', textAlign: 'right' }}>
                  <div style={{ display: 'inline-flex', gap: '5px' }}>
                    <span
                      className="cmd-tag"
                      onClick={() => onRunCommand(`graph ${sc.scenario_id}`)}
                      style={{ cursor: 'pointer', fontSize: '11px' }}
                    >
                      [3D Graph]
                    </span>
                    <span
                      className="cmd-tag"
                      onClick={() => onRunCommand(`inspect ${sc.scenario_id}`)}
                      style={{ cursor: 'pointer', fontSize: '11px' }}
                    >
                      [Inspect]
                    </span>
                    <span
                      className="cmd-tag"
                      onClick={() => onRunCommand(`communities ${sc.scenario_id}`)}
                      style={{ cursor: 'pointer', fontSize: '11px' }}
                    >
                      [Communities]
                    </span>
                    <span
                      className="cmd-tag"
                      onClick={() => onRunCommand(`anomaly ${sc.scenario_id}`)}
                      style={{ cursor: 'pointer', fontSize: '11px' }}
                    >
                      [Anomaly]
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: '12px',
          padding: '8px 0',
        }}
      >
        <button
          disabled={currentPage <= 1}
          onClick={() => onRunCommand(`scenarios ${currentPrefix || ''} ${currentPage - 1}`.trim())}
          style={{
            background: currentPage <= 1 ? '#0a1a10' : '#003314',
            border: '1px solid #00aa44',
            color: currentPage <= 1 ? '#446655' : '#00ff66',
            padding: '4px 12px',
            cursor: currentPage <= 1 ? 'not-allowed' : 'pointer',
            fontFamily: 'monospace',
          }}
        >
          &lt; PREVIOUS PAGE
        </button>

        <span style={{ color: '#94a3b8', fontSize: '12px' }}>
          PAGE <strong style={{ color: '#00ff66' }}>{currentPage}</strong> OF {totalPages}
        </span>

        <button
          disabled={currentPage >= totalPages}
          onClick={() => onRunCommand(`scenarios ${currentPrefix || ''} ${currentPage + 1}`.trim())}
          style={{
            background: currentPage >= totalPages ? '#0a1a10' : '#003314',
            border: '1px solid #00aa44',
            color: currentPage >= totalPages ? '#446655' : '#00ff66',
            padding: '4px 12px',
            cursor: currentPage >= totalPages ? 'not-allowed' : 'pointer',
            fontFamily: 'monospace',
          }}
        >
          NEXT PAGE &gt;
        </button>
      </div>
    </div>
  );
};
