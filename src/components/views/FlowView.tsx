import React from 'react';

interface StructuredIO {
  address: string;
  amount_btc: number;
  entity_cluster_id: string;
}

interface FlowData {
  txid: number;
  timestamp: string;
  scenario_id: string;
  script_type: string;
  total_input_btc: number;
  total_output_btc: number;
  fee_btc: number;
  fee_ratio_percent: number;
  inputs: StructuredIO[];
  outputs: StructuredIO[];
  network_telemetry: {
    relay_ip: string;
    node_type: string;
    country_code: string;
    asn: string;
    propagation_delta_ms: number;
  };
}

interface FlowViewProps {
  data: FlowData;
  txid: number | string;
  onRunCommand: (cmd: string) => void;
  onClose?: () => void;
}

export const FlowView: React.FC<FlowViewProps> = ({
  data,
  txid,
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
            &gt; FINANCIAL UTXO FLOW & CIOH ENTITY DECOMPOSITION
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
            TXID #{data.txid || txid}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '6px' }}>
          <span
            className="cmd-tag"
            onClick={() => onRunCommand(`inspect ${data.txid || txid}`)}
            style={{ cursor: 'pointer' }}
          >
            [Inspect]
          </span>
          <span
            className="cmd-tag"
            onClick={() => onRunCommand(`dossier ${data.txid || txid}`)}
            style={{ cursor: 'pointer' }}
          >
            [Dossier]
          </span>
          {data.scenario_id && (
            <span
              className="cmd-tag"
              onClick={() => onRunCommand(`graph ${data.scenario_id}`)}
              style={{ cursor: 'pointer' }}
            >
              [3D Graph]
            </span>
          )}
          {onClose && (
            <span className="cmd-tag" onClick={onClose} style={{ cursor: 'pointer' }}>
              [Close]
            </span>
          )}
        </div>
      </div>

      {/* Overview Stat Bar */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '10px',
          marginBottom: '16px',
        }}
      >
        <div style={{ border: '1px solid #0284c7', background: '#021626', padding: '10px' }}>
          <div style={{ color: '#7dd3fc', fontSize: '11px' }}>TOTAL INPUT VALUE</div>
          <div style={{ color: '#38bdf8', fontSize: '18px', fontWeight: 'bold' }}>
            {data.total_input_btc.toFixed(6)} BTC
          </div>
          <div style={{ color: '#64748b', fontSize: '10px' }}>{data.inputs?.length || 0} UTXO inputs</div>
        </div>

        <div style={{ border: '1px solid #059669', background: '#021f15', padding: '10px' }}>
          <div style={{ color: '#6ee7b7', fontSize: '11px' }}>TOTAL OUTPUT VALUE</div>
          <div style={{ color: '#34d399', fontSize: '18px', fontWeight: 'bold' }}>
            {data.total_output_btc.toFixed(6)} BTC
          </div>
          <div style={{ color: '#64748b', fontSize: '10px' }}>{data.outputs?.length || 0} outputs generated</div>
        </div>

        <div style={{ border: '1px solid #eab308', background: '#1c1503', padding: '10px' }}>
          <div style={{ color: '#fde047', fontSize: '11px' }}>MINER TRANSACTION FEE</div>
          <div style={{ color: '#fbbf24', fontSize: '18px', fontWeight: 'bold' }}>
            {data.fee_btc.toFixed(6)} BTC
          </div>
          <div style={{ color: '#b45309', fontSize: '10px' }}>Fee Ratio: {data.fee_ratio_percent.toFixed(3)}%</div>
        </div>

        <div style={{ border: '1px solid #a855f7', background: '#160824', padding: '10px' }}>
          <div style={{ color: '#d8b4fe', fontSize: '11px' }}>SCRIPT & TIMING</div>
          <div style={{ color: '#c084fc', fontSize: '16px', fontWeight: 'bold' }}>
            {data.script_type || 'P2PKH'}
          </div>
          <div style={{ color: '#7e22ce', fontSize: '10px' }}>{data.timestamp}</div>
        </div>
      </div>

      {/* Interactive Flow Decomposition Columns */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr auto 1fr',
          gap: '12px',
          alignItems: 'stretch',
          marginBottom: '16px',
        }}
      >
        {/* Left: Inputs */}
        <div style={{ border: '1px solid #0284c7', background: '#020d18', padding: '12px' }}>
          <div style={{ color: '#38bdf8', fontWeight: 'bold', fontSize: '13px', marginBottom: '8px' }}>
            INPUT UTXOS ({data.inputs?.length || 0})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {data.inputs?.map((inp, idx) => (
              <div
                key={idx}
                style={{
                  border: '1px solid #03446a',
                  background: '#031626',
                  padding: '8px',
                  borderRadius: '2px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span
                    className="cmd-clickable"
                    onClick={() => onRunCommand(`inspect ${inp.address}`)}
                    style={{ color: '#38bdf8', fontWeight: 'bold', fontSize: '12px' }}
                  >
                    {inp.address}
                  </span>
                  <span style={{ color: '#fff', fontWeight: 'bold', fontSize: '12px' }}>
                    {inp.amount_btc.toFixed(6)} BTC
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#94a3b8' }}>
                  <span>CIOH ENTITY: <strong style={{ color: '#a78bfa' }}>{inp.entity_cluster_id}</strong></span>
                  <span className="cmd-tag" onClick={() => onRunCommand(`taint ${inp.address}`)} style={{ fontSize: '9px' }}>
                    [Taint]
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Center Flow Indicator */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '10px',
            color: '#00ff66',
          }}
        >
          <div style={{ fontSize: '20px' }}>➔</div>
          <div style={{ fontSize: '10px', color: '#fbbf24', marginTop: '4px', textAlign: 'center' }}>
            FEE<br />
            {data.fee_btc.toFixed(5)} BTC
          </div>
        </div>

        {/* Right: Outputs */}
        <div style={{ border: '1px solid #059669', background: '#01120b', padding: '12px' }}>
          <div style={{ color: '#34d399', fontWeight: 'bold', fontSize: '13px', marginBottom: '8px' }}>
            OUTPUT RECIPIENTS ({data.outputs?.length || 0})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {data.outputs?.map((out, idx) => (
              <div
                key={idx}
                style={{
                  border: '1px solid #065f46',
                  background: '#021f15',
                  padding: '8px',
                  borderRadius: '2px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span
                    className="cmd-clickable"
                    onClick={() => onRunCommand(`inspect ${out.address}`)}
                    style={{ color: '#34d399', fontWeight: 'bold', fontSize: '12px' }}
                  >
                    {out.address}
                  </span>
                  <span style={{ color: '#fff', fontWeight: 'bold', fontSize: '12px' }}>
                    {out.amount_btc.toFixed(6)} BTC
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#94a3b8' }}>
                  <span>CIOH ENTITY: <strong style={{ color: '#a78bfa' }}>{out.entity_cluster_id}</strong></span>
                  <span className="cmd-tag" onClick={() => onRunCommand(`taint ${out.address}`)} style={{ fontSize: '9px' }}>
                    [Taint]
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Pre-Block Network Telemetry Footer */}
      {data.network_telemetry && (
        <div
          style={{
            border: '1px solid #00aa44',
            background: '#011508',
            padding: '10px 14px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px',
            fontSize: '12px',
          }}
        >
          <div>
            <span style={{ color: '#77aa88' }}>BROADCAST RELAY IP:</span>{' '}
            <strong style={{ color: '#fff' }}>{data.network_telemetry.relay_ip}</strong>
          </div>
          <div>
            <span style={{ color: '#77aa88' }}>INFRASTRUCTURE TYPE:</span>{' '}
            <strong
              style={{
                color: data.network_telemetry.node_type === 'tor' ? '#f43f5e' : '#38bdf8',
              }}
            >
              {data.network_telemetry.node_type?.toUpperCase()}
            </strong>
          </div>
          <div>
            <span style={{ color: '#77aa88' }}>ORIGIN ASN:</span>{' '}
            <span
              className="cmd-clickable"
              onClick={() => onRunCommand(`search ${data.network_telemetry.asn}`)}
              style={{ color: '#c084fc' }}
            >
              {data.network_telemetry.asn}
            </span>
          </div>
          <div>
            <span style={{ color: '#77aa88' }}>JURISDICTION:</span>{' '}
            <strong style={{ color: '#fbbf24' }}>{data.network_telemetry.country_code}</strong>
          </div>
          <div>
            <span style={{ color: '#77aa88' }}>PROPAGATION Δt:</span>{' '}
            <strong style={{ color: '#33ff88' }}>{data.network_telemetry.propagation_delta_ms} ms</strong>
          </div>
        </div>
      )}
    </div>
  );
};
