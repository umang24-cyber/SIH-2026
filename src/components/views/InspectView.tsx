import React from 'react';
import { ForensicNode } from '../../types/terminal';
import { MOCK_HEX_DUMPS } from '../../data/mockForensicData';

interface InspectViewProps {
  node: ForensicNode;
  onRunCommand: (cmd: string) => void;
}

export const InspectView: React.FC<InspectViewProps> = ({ node, onRunCommand }) => {
  const hexLines = MOCK_HEX_DUMPS[node.id] || [
    '00000000  7f 45 4c 46 02 01 01 00  00 00 00 00 00 00 00 00  |.ELF............|',
    '00000010  03 00 3e 00 01 00 00 00  a0 14 00 00 00 00 00 00  |..>.............|',
    '00000020  40 00 00 00 00 00 00 00  78 3b 00 00 00 00 00 00  |@.......x;......|',
    '00000030  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|',
    '00000040  06 00 00 00 04 00 00 00  40 00 00 00 00 00 00 00  |........@.......|',
    `00000050  ${node.id.slice(2, 4)} ${node.id.slice(4, 6)} ${node.id.slice(6, 8)} ${node.id.slice(8, 10)} 00 00 00 00  00 00 00 00 00 00 00 00  |..TARGET.DOSS...|`
  ];

  const getRiskBadge = (score: number) => {
    if (score >= 80) return <span className="badge badge-risk-high">CRITICAL RISK ({score}/100)</span>;
    if (score >= 50) return <span className="badge badge-risk-med">ELEVATED RISK ({score}/100)</span>;
    return <span className="badge badge-risk-low">LOW RISK ({score}/100)</span>;
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      <div style={{ borderBottom: '1px solid #00ff66', paddingBottom: '6px', marginBottom: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
        <h2 style={{ fontSize: '18px', color: '#33ff88' }}>
          &gt; FORENSIC DOSSIER &amp; HEX INSPECTOR :: {node.id}
        </h2>
        <div>{getRiskBadge(node.riskScore)}</div>
      </div>

      {/* Grid of metadata */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '12px', marginBottom: '16px' }}>
        <div style={{ border: '1px solid #007a33', padding: '10px', background: '#000c04' }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '6px', borderBottom: '1px dashed #004d20', paddingBottom: '4px' }}>
            ENTITY CLASSIFICATION
          </div>
          <p><strong>ENTITY ID:</strong> <span style={{ color: '#33ff88' }}>{node.id}</span></p>
          <p><strong>ALIAS / LABEL:</strong> {node.label}</p>
          <p><strong>ENTITY TYPE:</strong> <span style={{ color: '#00ff66' }}>{node.type}</span></p>
          <p><strong>AFFILIATION:</strong> {node.ownerAlias || 'UNMAPPED / ANONYMOUS'}</p>
          <p><strong>CLUSTER ID:</strong> <span style={{ color: '#33ff88' }}>{node.clusterId}</span></p>
        </div>

        <div style={{ border: '1px solid #007a33', padding: '10px', background: '#000c04' }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '6px', borderBottom: '1px dashed #004d20', paddingBottom: '4px' }}>
            LEDGER &amp; TELEMETRY
          </div>
          <p><strong>CURRENT UTXO BALANCE:</strong> <span style={{ color: '#33ff88' }}>{(node.balanceBtc ?? node.balanceEth ?? 0).toLocaleString()} BTC</span></p>
          <p><strong>TX LIFETIME COUNT:</strong> {node.txCount.toLocaleString()} transactions</p>
          <p><strong>FIRST SEEN:</strong> {node.firstSeen}</p>
          <p><strong>LAST OBSERVED:</strong> {node.lastSeen}</p>
        </div>
      </div>

      {/* Forensic Flags */}
      <div style={{ border: '1px solid #007a33', padding: '10px', background: '#000c04', marginBottom: '16px' }}>
        <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '6px' }}>
          DETECTED HEURISTIC FLAGS &amp; AML INDICATORS
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {node.flags.map(f => (
            <span key={f} style={{ background: '#00220a', border: '1px solid #00ff66', padding: '2px 8px', fontSize: '13px', color: '#33ff88' }}>
              ⚠ {f}
            </span>
          ))}
          {node.tags.map(t => (
            <span key={t} style={{ background: '#001406', border: '1px solid #007a33', padding: '2px 8px', fontSize: '13px', color: '#00ff66' }}>
              #{t}
            </span>
          ))}
        </div>
      </div>

      {/* Raw Memory Hexdump */}
      <div style={{ border: '1px solid #007a33', padding: '10px', background: '#000502', marginBottom: '16px' }}>
        <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '6px', display: 'flex', justifyContent: 'space-between' }}>
          <span>RAW BITCOIN SCRIPT / TRANSACTION BYTECODE (/proc/bitkaun/raw_tx/{node.id.slice(0, 10)})</span>
          <span style={{ fontSize: '13px', color: '#007a33' }}>OFFSET: 0x00000000 - 0x00000050</span>
        </div>
        <pre style={{ fontFamily: 'var(--font-code)', fontSize: '13px', color: '#00ff66', overflowX: 'auto', lineHeight: 1.4 }}>
          {hexLines.join('\n')}
        </pre>
      </div>

      {/* Quick Navigation Commands */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', fontSize: '15px' }}>
        <span style={{ color: '#007a33' }}>Available Actions:</span>
        <span className="cmd-clickable" onClick={() => onRunCommand('graph')}>
          [Switch to 3D Graph]
        </span>
        <span className="cmd-clickable" onClick={() => onRunCommand(`trace ${node.id} 1s6D1TaSbKqeTG5YMhWWRJ85Ve8s7Y`)}>
          [Trace to Cashout OTC: 1s6D1TaSbKqeTG5YMhWWRJ85Ve8s7Y]
        </span>
        <span className="cmd-clickable" onClick={() => onRunCommand('dmesg')}>
          [View Kernel Logs]
        </span>
        <span className="cmd-clickable" onClick={() => onRunCommand('home')}>
          [Return Home]
        </span>
      </div>
    </div>
  );
};
