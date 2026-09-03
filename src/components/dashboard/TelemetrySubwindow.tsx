import React from 'react';
import { GraphNode, ForensicScenario } from '../../data/forensicScenarios';

interface TelemetrySubwindowProps {
  selectedNode: GraphNode | null;
  scenario: ForensicScenario;
  onMinimize: () => void;
  onClose: () => void;
  style?: React.CSSProperties;
}

export const TelemetrySubwindow: React.FC<TelemetrySubwindowProps> = ({
  selectedNode,
  scenario,
  onMinimize,
  onClose,
  style
}) => {
  const targetNode = selectedNode || scenario.nodes.find(n => n.type === 'Transaction') || scenario.nodes[0];

  return (
    <div
      className="tui-subwindow"
      style={{
        width: '420px',
        maxHeight: '480px',
        ...style
      }}
    >
      {/* Retro Window Header */}
      <div className="tui-window-titlebar">
        <span>┌─[ WIN_02: DUAL_TELEMETRY.dossier ]</span>
        <div className="window-ctrls">
          <span className="window-ctrl-btn" onClick={onMinimize} title="Minimize">
            [—]
          </span>
          <span className="window-ctrl-btn" onClick={onClose} title="Close">
            [x]
          </span>
        </div>
      </div>

      <div className="tui-window-body">
        {/* Node Identity Banner */}
        <div style={{ background: '#021a08', padding: '8px 10px', marginBottom: '12px', borderLeft: '3px solid #00ff66', borderRadius: '2px' }}>
          <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600 }}>INSPECTED ENTITY</div>
          <div style={{ fontSize: '14px', fontWeight: 800, color: '#ffffff', wordBreak: 'break-all', marginTop: '2px' }}>
            {targetNode.id}
          </div>
          <div style={{ fontSize: '12px', color: '#00ff66', marginTop: '4px', fontWeight: 700 }}>
            CLASSIFICATION: {targetNode.type.toUpperCase()}
          </div>
        </div>

        {/* LAYER 1: ON-CHAIN FINANCIAL UTXO LEDGER */}
        <div className="telemetry-section-title">
          LAYER 1: ON-CHAIN UTXO FINANCIAL LEDGER
        </div>

        {targetNode.type === 'Wallet' && (
          <div>
            <div className="telemetry-row">
              <span className="telemetry-label">Full Address:</span>
              <span className="telemetry-value">{targetNode.properties.address}</span>
            </div>
            <div className="telemetry-row">
              <span className="telemetry-label">Holding Balance:</span>
              <span className="telemetry-value" style={{ color: '#00ff66' }}>{targetNode.properties.balance_btc} BTC</span>
            </div>
            <div className="telemetry-row">
              <span className="telemetry-label">Entity Status:</span>
              <span className="telemetry-value" style={{ color: targetNode.properties.is_licit_exchange ? '#00aaff' : '#ffaa00' }}>
                {targetNode.properties.is_licit_exchange ? 'VERIFIED_EXCHANGE (LICIT)' : 'PRIVATE_UNLICENSED_ADDRESS'}
              </span>
            </div>
          </div>
        )}

        {targetNode.type === 'Transaction' && (
          <div>
            <div className="telemetry-row">
              <span className="telemetry-label">Transaction ID:</span>
              <span className="telemetry-value">{targetNode.properties.txid}</span>
            </div>
            <div className="telemetry-row">
              <span className="telemetry-label">Ledger Timestamp:</span>
              <span className="telemetry-value">{targetNode.properties.timestamp}</span>
            </div>
            <div className="telemetry-row">
              <span className="telemetry-label">Mining Network Fee:</span>
              <span className="telemetry-value">{targetNode.properties.fee_btc} BTC</span>
            </div>
            <div className="telemetry-row">
              <span className="telemetry-label">Script Encoding:</span>
              <span className="telemetry-value" style={{ color: '#00ff66' }}>{targetNode.properties.script_type}</span>
            </div>
          </div>
        )}

        {targetNode.type === 'IP' && (
          <div>
            <div className="telemetry-row">
              <span className="telemetry-label">Relay Port:</span>
              <span className="telemetry-value">{targetNode.properties.relay_port || 8333}</span>
            </div>
            <div className="telemetry-row">
              <span className="telemetry-label">Target Broadcast:</span>
              <span className="telemetry-value">Bitcoin P2P Mainnet</span>
            </div>
          </div>
        )}

        {/* LAYER 2: P2P NETWORK BROADCAST METADATA */}
        <div className="telemetry-section-title" style={{ marginTop: '16px' }}>
          LAYER 2: P2P NETWORK BROADCAST TELEMETRY
        </div>

        <div className="telemetry-row">
          <span className="telemetry-label">Origin Relay IP:</span>
          <span className="telemetry-value" style={{ color: '#00ff66' }}>
            {targetNode.properties.relay_ip || scenario.telemetry.origin_ips[0]}
          </span>
        </div>
        <div className="telemetry-row">
          <span className="telemetry-label">Autonomous System (ASN):</span>
          <span className="telemetry-value">
            {targetNode.properties.asn || scenario.telemetry.origin_asns[0]}
          </span>
        </div>
        <div className="telemetry-row">
          <span className="telemetry-label">Carrier / ISP:</span>
          <span className="telemetry-value">
            {targetNode.properties.isp || 'Identified Carrier Gateway'}
          </span>
        </div>
        <div className="telemetry-row">
          <span className="telemetry-label">Country Jurisdiction:</span>
          <span className="telemetry-value">
            [{targetNode.properties.country_code || scenario.telemetry.countries[0]}] Route Confirmed
          </span>
        </div>
        <div className="telemetry-row">
          <span className="telemetry-label">Infrastructure Type:</span>
          <span
            className="telemetry-value"
            style={{
              color:
                targetNode.properties.node_type === 'bulletproof_host'
                  ? '#ff4444'
                  : targetNode.properties.node_type === 'tor_exit'
                  ? '#cc66ff'
                  : '#00ff66'
            }}
          >
            {(targetNode.properties.node_type || Object.keys(scenario.telemetry.infrastructure_distribution)[0] || 'residential').toUpperCase()}
          </span>
        </div>
        <div className="telemetry-row">
          <span className="telemetry-label">Propagation Latency:</span>
          <span className="telemetry-value" style={{ color: '#ffffff' }}>
            {targetNode.properties.propagation_delta_ms || 188} ms
          </span>
        </div>
      </div>
    </div>
  );
};
