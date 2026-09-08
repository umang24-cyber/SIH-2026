import React from 'react';

interface CommunityMember {
  id: string;
  type: string;
}

interface CommunityCluster {
  community_id: string;
  total_members: number;
  wallet_count: number;
  transaction_count: number;
  ip_count: number;
  members: CommunityMember[];
}

interface CommunitiesData {
  scenario_id: string;
  total_nodes: number;
  total_edges: number;
  total_communities_detected: number;
  communities: CommunityCluster[];
}

interface CommunitiesViewProps {
  data: CommunitiesData;
  scenarioId: string;
  onRunCommand: (cmd: string) => void;
  onClose?: () => void;
}

export const CommunitiesView: React.FC<CommunitiesViewProps> = ({
  data,
  scenarioId,
  onRunCommand,
  onClose,
}) => {
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '16px', color: '#33ff88', fontWeight: 'bold' }}>
            &gt; COMMUNITY DETECTION & MODULARITY PARTITION :: {data.scenario_id || scenarioId}
          </span>
          <span
            style={{
              padding: '2px 8px',
              borderRadius: '3px',
              fontSize: '11px',
              fontWeight: 'bold',
              border: '1px solid #38bdf8',
              color: '#38bdf8',
              background: 'rgba(0,0,0,0.4)',
            }}
          >
            {data.total_communities_detected} SYNDICATES / CLUSTERS DETECTED
          </span>
        </div>
        <div style={{ display: 'flex', gap: '6px' }}>
          <span
            className="cmd-tag"
            onClick={() => onRunCommand(`graph ${data.scenario_id || scenarioId}`)}
            style={{ cursor: 'pointer' }}
          >
            [Open 3D Graph]
          </span>
          {onClose && (
            <span className="cmd-tag" onClick={onClose} style={{ cursor: 'pointer' }}>
              [Close]
            </span>
          )}
        </div>
      </div>

      {/* Network Metrics Bar */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '10px',
          marginBottom: '16px',
        }}
      >
        <div style={{ border: '1px solid #00aa44', background: '#011508', padding: '10px' }}>
          <div style={{ color: '#77aa88', fontSize: '11px' }}>TOTAL GRAPH NODES</div>
          <div style={{ color: '#33ff88', fontSize: '18px', fontWeight: 'bold' }}>
            {data.total_nodes}
          </div>
        </div>

        <div style={{ border: '1px solid #0284c7', background: '#021626', padding: '10px' }}>
          <div style={{ color: '#7dd3fc', fontSize: '11px' }}>INTER-ENTITY EDGES</div>
          <div style={{ color: '#38bdf8', fontSize: '18px', fontWeight: 'bold' }}>
            {data.total_edges}
          </div>
        </div>

        <div style={{ border: '1px solid #a855f7', background: '#160824', padding: '10px' }}>
          <div style={{ color: '#d8b4fe', fontSize: '11px' }}>GREEDY MODULARITY PARTITIONS</div>
          <div style={{ color: '#c084fc', fontSize: '18px', fontWeight: 'bold' }}>
            {data.total_communities_detected}
          </div>
        </div>
      </div>

      {/* Communities Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {data.communities?.map((comm, idx) => {
          const isLarge = comm.total_members > 5;
          const borderColor = isLarge ? '#a855f7' : '#00aa44';
          const headerBg = isLarge ? '#20083b' : '#00260e';

          return (
            <div
              key={comm.community_id || idx}
              style={{
                border: `1px solid ${borderColor}`,
                background: '#020b05',
              }}
            >
              {/* Community Card Header */}
              <div
                style={{
                  background: headerBg,
                  padding: '8px 12px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '8px',
                  borderBottom: `1px solid ${borderColor}55`,
                }}
              >
                <div>
                  <span style={{ color: '#fff', fontWeight: 'bold', fontSize: '13px' }}>
                    COMMUNITY #{idx + 1}
                  </span>
                  <span style={{ color: '#94a3b8', fontSize: '11px', marginLeft: '10px' }}>
                    ID: {comm.community_id}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: '10px', fontSize: '11px' }}>
                  <span style={{ color: '#34d399' }}>
                    <strong>{comm.wallet_count}</strong> Wallets
                  </span>
                  <span style={{ color: '#38bdf8' }}>
                    <strong>{comm.transaction_count}</strong> Transactions
                  </span>
                  <span style={{ color: '#fbbf24' }}>
                    <strong>{comm.ip_count}</strong> IP Relays
                  </span>
                  <span style={{ color: '#fff', fontWeight: 'bold' }}>
                    ({comm.total_members} Total Members)
                  </span>
                </div>
              </div>

              {/* Members Preview */}
              <div style={{ padding: '12px' }}>
                <div style={{ color: '#77aa88', fontSize: '11px', marginBottom: '8px' }}>
                  KEY CO-ACTING ENTITY NODES (PREVIEW):
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {comm.members?.map((m) => {
                    const isTx = m.type === 'Transaction';
                    const isIP = m.type === 'IP';
                    const chipColor = isTx ? '#38bdf8' : isIP ? '#fbbf24' : '#34d399';
                    const chipBg = isTx ? '#031f33' : isIP ? '#261b03' : '#022415';

                    return (
                      <span
                        key={m.id}
                        className="cmd-clickable"
                        onClick={() => onRunCommand(`inspect ${m.id}`)}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '5px',
                          padding: '3px 8px',
                          border: `1px solid ${chipColor}55`,
                          background: chipBg,
                          borderRadius: '3px',
                          fontSize: '11px',
                          color: chipColor,
                          cursor: 'pointer',
                        }}
                        title={`Type: ${m.type} - Click to inspect`}
                      >
                        <span style={{ fontSize: '9px', opacity: 0.8 }}>[{m.type[0]}]</span>
                        <span>{m.id.length > 22 ? `${m.id.slice(0, 10)}...${m.id.slice(-8)}` : m.id}</span>
                      </span>
                    );
                  })}
                  {comm.total_members > comm.members?.length && (
                    <span style={{ color: '#64748b', fontSize: '11px', padding: '3px 6px' }}>
                      +{comm.total_members - comm.members.length} more nodes
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
