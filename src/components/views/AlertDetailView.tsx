import React from 'react';
import { EvidenceResponse, FeatureAttribution } from '../../services/api';

interface AlertDetailViewProps {
  evidence: EvidenceResponse;
  onRunCommand: (cmd: string) => void;
  onClose?: () => void;
}

export const AlertDetailView: React.FC<AlertDetailViewProps> = ({
  evidence,
  onRunCommand,
  onClose,
}) => {
  const pattern = (evidence.predicted_pattern_type || 'UNKNOWN').toUpperCase();
  const binConf = Number(evidence.binary_confidence ?? 0);
  const typConf = Number(evidence.typology_confidence ?? 0);
  const heuristic = evidence.typology_heuristic_match;
  const explanation = evidence.typology_explanation || 'No natural language explanation available.';
  const shapList: FeatureAttribution[] =
    evidence.ml_feature_attributions || evidence.typology_shap_attributions || [];
  const telem = evidence.telemetry_summary || {};
  const originIps = telem.origin_ips || [];
  const originAsns = telem.origin_asns || [];
  const countries = telem.countries || [];
  const infra = telem.infrastructure_distribution || {};

  const getPatternBadge = (type: string) => {
    switch (type) {
      case 'RANSOMWARE':
        return (
          <span style={{ background: '#ff3344', color: '#000', fontWeight: 800, padding: '2px 8px', borderRadius: '3px', fontSize: '12px' }}>
            RANSOMWARE
          </span>
        );
      case 'MIXING':
        return (
          <span style={{ background: '#d946ef', color: '#000', fontWeight: 800, padding: '2px 8px', borderRadius: '3px', fontSize: '12px' }}>
            MIXING / COINJOIN
          </span>
        );
      case 'LAYERING':
        return (
          <span style={{ background: '#f59e0b', color: '#000', fontWeight: 800, padding: '2px 8px', borderRadius: '3px', fontSize: '12px' }}>
            LAYERING
          </span>
        );
      case 'PEELING_CHAIN':
        return (
          <span style={{ background: '#06b6d4', color: '#000', fontWeight: 800, padding: '2px 8px', borderRadius: '3px', fontSize: '12px' }}>
            PEELING CHAIN
          </span>
        );
      default:
        return (
          <span style={{ background: '#00ff66', color: '#000', fontWeight: 800, padding: '2px 8px', borderRadius: '3px', fontSize: '12px' }}>
            {type}
          </span>
        );
    }
  };

  const primaryDest = heuristic?.primary_destination;
  const firstTxid = evidence.transactions?.[0]?.txid;

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', fontSize: '14px', lineHeight: '1.5' }}>
      {/* Title Bar */}
      <div style={{ borderBottom: '1px solid #00ff66', paddingBottom: '8px', marginBottom: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <span style={{ color: '#33ff88', fontWeight: 800, fontSize: '16px' }}>
            [*] DEEP FORENSIC EVIDENCE &amp; SHAP ATTRIBUTION DOSSIER
          </span>
          <div style={{ color: '#94a3b8', fontSize: '12px', marginTop: '2px' }}>
            CANDIDATE ID: <strong style={{ color: '#38bdf8' }}>{evidence.candidate_id}</strong>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {getPatternBadge(pattern)}
          {onClose && (
            <span className="cmd-tag" onClick={onClose} style={{ cursor: 'pointer' }}>
              [Close]
            </span>
          )}
        </div>
      </div>

      {/* Top Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '12px', marginBottom: '16px' }}>
        {/* Card 1: Risk & Model Metrics */}
        <div style={{ border: '1px solid #00aa44', padding: '12px', background: '#000c04' }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '8px', borderBottom: '1px dashed #004d20', paddingBottom: '4px' }}>
            MODEL INFERENCE &amp; CONFIDENCE SCORES
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }}>
            <div>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>BINARY RISK CONFIDENCE</div>
              <div style={{ fontSize: '18px', fontWeight: 800, color: binConf >= 0.7 ? '#ff3344' : '#ffaa00' }}>
                {(binConf * 100).toFixed(1)}%
              </div>
            </div>
            <div>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>TYPOLOGY CONFIDENCE</div>
              <div style={{ fontSize: '18px', fontWeight: 800, color: typConf >= 0.7 ? '#00ff66' : '#ffaa00' }}>
                {(typConf * 100).toFixed(1)}%
              </div>
            </div>
          </div>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>
            Scenario Context:{' '}
            <span
              className="cmd-clickable"
              onClick={() => onRunCommand(`graph ${evidence.scenario_id}`)}
              style={{ color: '#00ff66', fontWeight: 'bold' }}
            >
              {evidence.scenario_id}
            </span>
          </div>
        </div>

        {/* Card 2: Heuristic Corroboration */}
        <div style={{ border: '1px solid #00aa44', padding: '12px', background: '#000c04' }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '8px', borderBottom: '1px dashed #004d20', paddingBottom: '4px' }}>
            STRUCTURAL HEURISTIC CORROBORATION
          </div>
          {heuristic ? (
            <div style={{ fontSize: '13px', color: '#f8fafc' }}>
              <div>
                <strong>Heuristic:</strong>{' '}
                <span style={{ color: '#38bdf8' }}>{heuristic.heuristic_name || 'Substructure Traversal'}</span>
              </div>
              <div>
                <strong>Observed Chain Length:</strong> {heuristic.chain_length ?? 'N/A'} hops
              </div>
              {heuristic.reconvergence_detected !== undefined && (
                <div>
                  <strong>Reconvergence Detected:</strong>{' '}
                  <span style={{ color: heuristic.reconvergence_detected ? '#ff3344' : '#00ff66' }}>
                    {heuristic.reconvergence_detected ? 'YES (Fan-In Hub)' : 'NO'}
                  </span>
                </div>
              )}
              {primaryDest && (
                <div style={{ marginTop: '4px' }}>
                  <strong>Destination Wallet:</strong>{' '}
                  <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${primaryDest}`)}>
                    {primaryDest}
                  </span>
                </div>
              )}
            </div>
          ) : (
            <div style={{ color: '#94a3b8', fontSize: '13px' }}>
              No explicit structural heuristic rule recorded. ML-driven detection.
            </div>
          )}
        </div>
      </div>

      {/* Forensic Explanation Rationale Box */}
      <div style={{ border: '1px solid #00aa44', padding: '12px', background: '#000c04', marginBottom: '16px' }}>
        <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '6px' }}>
          NATURAL-LANGUAGE FORENSIC RATIONALE (TreeSHAP Synthesized)
        </div>
        <div style={{ color: '#f8fafc', fontSize: '13px', lineHeight: '1.6' }}>
          {explanation}
        </div>
      </div>

      {/* XGBoost / TreeSHAP Feature Attribution Table */}
      {shapList && shapList.length > 0 && (
        <div style={{ border: '1px solid #00aa44', padding: '12px', background: '#000c04', marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ color: '#33ff88', fontWeight: 'bold', fontSize: '14px' }}>
              [*] XGBoost / TreeSHAP Feature Attribution Breakdown
            </span>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>
              Top {Math.min(10, shapList.length)} Local Feature Attributions
            </span>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #00ff66', color: '#33ff88', textAlign: 'left' }}>
                <th style={{ padding: '6px' }}>Forensic Feature</th>
                <th style={{ padding: '6px', textAlign: 'right' }}>Feature Value</th>
                <th style={{ padding: '6px', textAlign: 'right' }}>SHAP Impact</th>
                <th style={{ padding: '6px', textAlign: 'center' }}>Direction / Risk Influence</th>
              </tr>
            </thead>
            <tbody>
              {shapList.slice(0, 10).map((item, idx) => {
                const sval = typeof item.shap_value === 'number' ? item.shap_value : parseFloat(item.shap_value || '0');
                const isElevating = (item.direction && item.direction.includes('INCREASING')) || sval > 0;
                const formattedVal =
                  typeof item.value === 'number'
                    ? (Number.isInteger(item.value) ? item.value : item.value.toFixed(4))
                    : String(item.value ?? 'N/A');

                return (
                  <tr key={idx} style={{ borderBottom: '1px solid #00220a' }}>
                    <td style={{ padding: '6px', color: '#38bdf8', fontFamily: 'monospace' }}>
                      {item.feature_name}
                    </td>
                    <td style={{ padding: '6px', textAlign: 'right', color: '#ffffff' }}>
                      {formattedVal}
                    </td>
                    <td style={{ padding: '6px', textAlign: 'right', color: isElevating ? '#ffaa00' : '#00ff66', fontWeight: 'bold' }}>
                      {sval >= 0 ? `+${sval.toFixed(4)}` : sval.toFixed(4)}
                    </td>
                    <td style={{ padding: '6px', textAlign: 'center' }}>
                      {isElevating ? (
                        <span style={{ color: '#ff3344', fontWeight: 'bold' }}>▲ ELEVATES RISK</span>
                      ) : (
                        <span style={{ color: '#00ff66', fontWeight: 'bold' }}>▼ LOWERS RISK</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* P2P Telemetry & Infrastructure Provenance */}
      <div style={{ border: '1px solid #00aa44', padding: '12px', background: '#000c04', marginBottom: '16px' }}>
        <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '8px' }}>
          [*] P2P Telemetry &amp; Infrastructure Provenance
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px', fontSize: '13px' }}>
          <div>
            <div style={{ color: '#94a3b8', fontSize: '11px' }}>ORIGIN IPS</div>
            <div>
              {originIps.length > 0 ? (
                originIps.map((ip: string, i: number) => (
                  <span
                    key={i}
                    className="cmd-clickable"
                    onClick={() => onRunCommand(`inspect ${ip}`)}
                    style={{ marginRight: '6px' }}
                  >
                    {ip}
                  </span>
                ))
              ) : (
                <span style={{ color: '#94a3b8' }}>None recorded</span>
              )}
            </div>
          </div>
          <div>
            <div style={{ color: '#94a3b8', fontSize: '11px' }}>ORIGIN ASNS</div>
            <div style={{ color: '#f59e0b' }}>
              {originAsns.length > 0 ? originAsns.join(', ') : 'None recorded'}
            </div>
          </div>
          <div>
            <div style={{ color: '#94a3b8', fontSize: '11px' }}>COUNTRIES</div>
            <div style={{ color: '#ffffff' }}>
              {countries.length > 0 ? countries.join(', ') : 'Unknown'}
            </div>
          </div>
          <div>
            <div style={{ color: '#94a3b8', fontSize: '11px' }}>INFRASTRUCTURE NODES</div>
            <div style={{ color: '#d946ef', fontWeight: 'bold' }}>
              {Object.keys(infra).length > 0
                ? Object.entries(infra).map(([k, v]) => `${k}: ${v}`).join(' · ')
                : 'Residential default'}
            </div>
          </div>
        </div>
      </div>

      {/* Action Toolbar */}
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', paddingTop: '6px', borderTop: '1px solid #004d20' }}>
        <span
          className="cmd-tag"
          onClick={() => onRunCommand('alerts')}
          style={{ cursor: 'pointer', padding: '4px 10px', background: '#00220a', border: '1px solid #00aa44' }}
        >
          [← Back to Alerts Feed]
        </span>
        <span
          className="cmd-tag"
          onClick={() => onRunCommand(`graph ${evidence.scenario_id}`)}
          style={{ cursor: 'pointer', padding: '4px 10px', background: '#00220a', border: '1px solid #00aa44' }}
        >
          [🌐 Open 3D Scenario Graph]
        </span>
        {primaryDest && (
          <span
            className="cmd-tag"
            onClick={() => onRunCommand(`inspect ${primaryDest}`)}
            style={{ cursor: 'pointer', padding: '4px 10px', background: '#00220a', border: '1px solid #00aa44' }}
          >
            [👤 Inspect Primary Wallet]
          </span>
        )}
        {firstTxid && (
          <span
            className="cmd-tag"
            onClick={() => onRunCommand(`dossier ${firstTxid}`)}
            style={{ cursor: 'pointer', padding: '4px 10px', background: '#00220a', border: '1px solid #00aa44' }}
          >
            [📄 Generate Case Dossier]
          </span>
        )}
      </div>
    </div>
  );
};
