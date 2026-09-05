import React from 'react';
import { GraphNode, ForensicScenario } from '../../data/forensicScenarios';
import type { GraphData } from "../../types/graph";

interface TelemetrySubwindowProps {
  selectedNode: GraphNode | null;
  scenario: ForensicScenario;
  graphData: GraphData;
  onMinimize: () => void;
  onClose: () => void;
  style?: React.CSSProperties;
}

export const TelemetrySubwindow: React.FC<TelemetrySubwindowProps> = ({
  selectedNode,
  scenario,
  graphData,
  onMinimize,
  onClose,
  style
}) => {
  const targetNode = selectedNode || scenario.nodes.find(n => n.type === 'Transaction') || scenario.nodes[0];
  const adaptedNode =
  graphData.nodes.find(
    (node) => node.id === targetNode.id
  ) ?? null;
  const transactionAmount =
  targetNode.type === 'Transaction'
    ? scenario.edges
        .filter(
          (edge) =>
            edge.source === targetNode.id &&
            edge.type === 'RECEIVED'
        )
        .reduce(
          (total, edge) =>
            total + (edge.amount_btc || 0),
          0
        )
    : 0;
  const transactionCount =
  targetNode.type === "Wallet"
    ? graphData.edges.filter(
        edge =>
          edge.source === targetNode.id ||
          edge.target === targetNode.id
      ).length
    : 0;

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
      <span className="telemetry-label">
        Full Address:
      </span>

      <span className="telemetry-value">
        {targetNode.properties.address}
      </span>
    </div>

    <div className="telemetry-row">
      <span className="telemetry-label">
        Transaction Count:
      </span>

      <span
        className="telemetry-value"
        style={{ color: '#00ff66' }}
      >
        {transactionCount}
      </span>
    </div>

    <div className="telemetry-row">
  <span className="telemetry-label">
    Risk Score:
  </span>

  <span
    className="telemetry-value"
    style={{
      color:
        adaptedNode?.type === "WALLET"
          ? (adaptedNode.riskScore ?? 0) >= 0.8
            ? "#ff4444"
            : (adaptedNode.riskScore ?? 0) >= 0.5
            ? "#ff9900"
            : "#00ff66"
          : "#ffffff",
    }}
  >
    {adaptedNode?.type === "WALLET"
      ? adaptedNode.riskScore?.toFixed(2) ?? "N/A"
      : "N/A"}
  </span>
</div>

    <div className="telemetry-row">
      <span className="telemetry-label">
        Tags:
      </span>

      <span className="telemetry-value">
  {adaptedNode?.type === "WALLET"
    ? adaptedNode.tags?.length
      ? adaptedNode.tags.join(", ")
      : "None"
    : "None"}
</span>
    </div>

        <div className="telemetry-row">
      <span className="telemetry-label">
        Cluster ID:
      </span>

      <span className="telemetry-value">
        {adaptedNode?.type === "WALLET"
          ? adaptedNode.clusterId ?? "N/A"
          : "N/A"}
      </span>
    </div>
  </div>
)}

        {targetNode.type === 'Transaction' && (
  <div>
    <div className="telemetry-row">
      <span className="telemetry-label">Transaction ID:</span>
      <span className="telemetry-value">
        {targetNode.properties.txid}
      </span>
    </div>

    <div className="telemetry-row">
  <span className="telemetry-label">Amount:</span>
  <span
    className="telemetry-value"
    style={{ color: '#00ff66' }}
  >
    {transactionAmount.toFixed(4)} BTC
  </span>
</div>

    <div className="telemetry-row">
      <span className="telemetry-label">Fee:</span>
      <span className="telemetry-value">
        {targetNode.properties.fee_btc} BTC
      </span>
    </div>

    <div className="telemetry-row">
      <span className="telemetry-label">Timestamp:</span>
      <span className="telemetry-value">
        {targetNode.properties.timestamp}
      </span>
    </div>

    <div className="telemetry-row">
      <span className="telemetry-label">Script Encoding:</span>
      <span
        className="telemetry-value"
        style={{ color: '#00ff66' }}
      >
        {targetNode.properties.script_type}
      </span>
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
