import React from 'react';

interface AnomalyData {
  scenario_id: string;
  anomaly_score?: number;
  isolation_forest_score?: number;
  anomaly_label?: string;
  anomaly_level?: string;
  anomaly_raw_if_score?: number;
  anomaly_high_threshold?: number;
  anomaly_interpretation?: string;
  message?: string;
  n_transactions?: number;
  mean_propagation_delta_ms?: number;
  suspicious_node_ratio?: number;
}

interface AnomalyViewProps {
  data: AnomalyData;
  scenarioId: string;
  onRunCommand: (cmd: string) => void;
  onClose?: () => void;
}

export const AnomalyView: React.FC<AnomalyViewProps> = ({
  data,
  scenarioId,
  onRunCommand,
  onClose,
}) => {
  const score = data.anomaly_score ?? data.isolation_forest_score ?? 0;
  const level = (data.anomaly_label || data.anomaly_level || 'LOW').toUpperCase();
  const interpretation = data.anomaly_interpretation || data.message || 'Anomaly evaluated against reference distribution.';

  const getLevelColor = () => {
    switch (level) {
      case 'HIGH':
        return '#f43f5e';
      case 'MEDIUM':
        return '#fbbf24';
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '16px', color: '#33ff88', fontWeight: 'bold' }}>
            &gt; ISOLATION FOREST ANOMALY & UNUSUALNESS AUDIT
          </span>
          <span
            style={{
              padding: '2px 8px',
              borderRadius: '3px',
              fontSize: '11px',
              fontWeight: 'bold',
              border: `1px solid ${getLevelColor()}`,
              color: getLevelColor(),
              background: 'rgba(0,0,0,0.4)',
            }}
          >
            SCENARIO: {data.scenario_id || scenarioId} // {level} ANOMALY
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
          <span
            className="cmd-tag"
            onClick={() => onRunCommand(`communities ${data.scenario_id || scenarioId}`)}
            style={{ cursor: 'pointer' }}
          >
            [Communities]
          </span>
          {onClose && (
            <span className="cmd-tag" onClick={onClose} style={{ cursor: 'pointer' }}>
              [Close]
            </span>
          )}
        </div>
      </div>

      {/* Main Scorecard Gauge */}
      <div
        style={{
          border: `1px solid ${getLevelColor()}`,
          background: '#020d06',
          padding: '16px',
          marginBottom: '16px',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '10px',
            flexWrap: 'wrap',
            gap: '10px',
          }}
        >
          <div>
            <div style={{ color: '#94a3b8', fontSize: '12px' }}>ISOLATION FOREST ANOMALY SCORE</div>
            <div style={{ fontSize: '36px', fontWeight: 'bold', color: getLevelColor() }}>
              {score} <span style={{ fontSize: '16px', color: '#64748b' }}>/ 100</span>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span
              style={{
                fontSize: '14px',
                fontWeight: 'bold',
                color: getLevelColor(),
                border: `1px solid ${getLevelColor()}`,
                padding: '4px 12px',
                borderRadius: '3px',
                background: `${getLevelColor()}15`,
              }}
            >
              {level} UNUSUALNESS
            </span>
            <div style={{ color: '#94a3b8', fontSize: '11px', marginTop: '6px' }}>
              Independent Isolation Forest Metric
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div style={{ height: '8px', background: '#1e293b', borderRadius: '4px', overflow: 'hidden', marginBottom: '10px' }}>
          <div style={{ width: `${score}%`, height: '100%', background: getLevelColor() }} />
        </div>

        <div style={{ color: '#cbd5e1', fontSize: '12px', lineHeight: '1.5' }}>
          {interpretation}
        </div>
      </div>

      {/* Auxiliary Metric Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '12px',
          marginBottom: '16px',
        }}
      >
        <div style={{ border: '1px solid #00aa44', background: '#011508', padding: '12px' }}>
          <div style={{ color: '#77aa88', fontSize: '11px' }}>RAW DECISION FUNCTION SCORE</div>
          <div style={{ color: '#33ff88', fontSize: '20px', fontWeight: 'bold', marginTop: '2px' }}>
            {data.anomaly_raw_if_score !== undefined ? data.anomaly_raw_if_score.toFixed(4) : (data.n_transactions ? `${data.n_transactions} TXs` : '0.0000')}
          </div>
          <div style={{ color: '#558866', fontSize: '10px' }}>Raw forest outlier margin</div>
        </div>

        <div style={{ border: '1px solid #0284c7', background: '#021626', padding: '12px' }}>
          <div style={{ color: '#7dd3fc', fontSize: '11px' }}>HIGH ANOMALY THRESHOLD</div>
          <div style={{ color: '#38bdf8', fontSize: '20px', fontWeight: 'bold', marginTop: '2px' }}>
            {data.anomaly_high_threshold !== undefined ? data.anomaly_high_threshold.toFixed(2) : '70.00'}
          </div>
          <div style={{ color: '#64748b', fontSize: '10px' }}>Decision boundary cutoff</div>
        </div>

        <div style={{ border: '1px solid #eab308', background: '#1c1503', padding: '12px' }}>
          <div style={{ color: '#fde047', fontSize: '11px' }}>SUSPICIOUS RELAY ACTIVITY</div>
          <div style={{ color: '#fbbf24', fontSize: '20px', fontWeight: 'bold', marginTop: '2px' }}>
            {data.suspicious_node_ratio !== undefined ? `${(data.suspicious_node_ratio * 100).toFixed(1)}%` : (data.mean_propagation_delta_ms ? `${data.mean_propagation_delta_ms.toFixed(0)} ms` : 'EVALUATED')}
          </div>
          <div style={{ color: '#b45309', fontSize: '10px', marginTop: '2px' }}>
            Infrastructure anomaly weighting
          </div>
        </div>
      </div>

      {/* Forensic Disambiguation Note */}
      <div
        style={{
          border: '1px solid #334155',
          background: '#0a0f18',
          padding: '12px 14px',
          fontSize: '11px',
          color: '#94a3b8',
          lineHeight: '1.6',
        }}
      >
        <strong style={{ color: '#38bdf8' }}>SIH PS146 COMPLIANCE NOTE:</strong> The Isolation Forest Anomaly Score measures structural and temporal unusualness relative to normal (licit) Bitcoin behavior. It is <em>not</em> an illicit probability and is not combined with the XGBoost binary risk score or typology confidence.
      </div>
    </div>
  );
};
