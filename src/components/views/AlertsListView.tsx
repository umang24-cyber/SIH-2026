import React, { useState } from 'react';
import { AlertSummary } from '../../services/api';

interface AlertsListViewProps {
  content: any;
  onRunCommand: (cmd: string) => void;
  onClose?: () => void;
}

export const AlertsListView: React.FC<AlertsListViewProps> = ({
  content,
  onRunCommand,
  onClose,
}) => {
  const [filterType, setFilterType] = useState<string>('ALL');

  const alertList: AlertSummary[] = Array.isArray(content)
    ? content
    : (content?.alerts || []);
  const total = content?.total_alerts || alertList.length;

  const filteredAlerts = alertList.filter(a => {
    if (filterType === 'ALL') return true;
    const pat = (a.predicted_pattern_type || '').toLowerCase();
    const filter = filterType.toLowerCase();
    if (filter === 'mixing') return pat.includes('mix') || pat.includes('coinjoin');
    if (filter === 'peeling_chain') return pat.includes('peel');
    if (filter === 'layering') return pat.includes('layer');
    if (filter === 'ransomware') return pat.includes('ransom');
    return pat === filter;
  });

  const getPatternBadge = (pattern: string) => {
    const p = (pattern || '').toUpperCase();
    if (p.includes('RANSOM')) {
      return (
        <span style={{ background: '#ff3344', color: '#000', fontWeight: 800, padding: '2px 7px', borderRadius: '3px', fontSize: '11px', letterSpacing: '0.5px' }}>
          RANSOMWARE
        </span>
      );
    }
    if (p.includes('MIX') || p.includes('COINJOIN')) {
      return (
        <span style={{ background: '#d946ef', color: '#000', fontWeight: 800, padding: '2px 7px', borderRadius: '3px', fontSize: '11px', letterSpacing: '0.5px' }}>
          MIXING / COINJOIN
        </span>
      );
    }
    if (p.includes('LAYER')) {
      return (
        <span style={{ background: '#f59e0b', color: '#000', fontWeight: 800, padding: '2px 7px', borderRadius: '3px', fontSize: '11px', letterSpacing: '0.5px' }}>
          LAYERING
        </span>
      );
    }
    if (p.includes('PEEL')) {
      return (
        <span style={{ background: '#06b6d4', color: '#000', fontWeight: 800, padding: '2px 7px', borderRadius: '3px', fontSize: '11px', letterSpacing: '0.5px' }}>
          PEELING CHAIN
        </span>
      );
    }
    return (
      <span style={{ background: '#00ff66', color: '#000', fontWeight: 800, padding: '2px 7px', borderRadius: '3px', fontSize: '11px' }}>
        {p}
      </span>
    );
  };

  return (
    <div className="output-block" style={{ background: 'var(--bg-card)', border: '1px solid #00aa44', padding: '14px', maxWidth: '1150px', margin: '0 auto' }}>
      {/* Top Banner Panel */}
      <div style={{ borderBottom: '1px solid #00ff66', paddingBottom: '10px', marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <div style={{ color: '#33ff88', fontWeight: 800, fontSize: '16px', letterSpacing: '0.5px' }}>
            [*] PRIORITIZED AML FORENSIC ALERT FEED
          </div>
          <div style={{ marginTop: '4px', fontSize: '12px' }}>
            <span style={{ color: '#ffffff' }}>Active Alerts Monitored:</span>{' '}
            <strong style={{ color: '#ff3344' }}>{total.toLocaleString()}</strong>
            <span style={{ color: '#94a3b8', margin: '0 8px' }}>|</span>
            <span style={{ color: '#ffffff' }}>Displaying Top:</span>{' '}
            <strong style={{ color: '#ffaa00' }}>{filteredAlerts.length}</strong>
            <span style={{ color: '#94a3b8', margin: '0 8px' }}>|</span>
            <span style={{ color: '#94a3b8' }}>Inspect full evidence with:</span>{' '}
            <code style={{ color: '#38bdf8', fontSize: '11px' }}>alerts --detail &lt;candidate_id&gt;</code>
          </div>
        </div>

        {onClose && (
          <span className="cmd-tag" onClick={onClose} style={{ cursor: 'pointer' }}>
            [Close]
          </span>
        )}
      </div>

      {/* Filter Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          marginBottom: '14px',
          fontSize: '12px',
          flexWrap: 'wrap',
          alignItems: 'center',
        }}
      >
        <span style={{ color: '#94a3b8', fontSize: '11px', textTransform: 'uppercase' }}>Filter Typology:</span>
        {['ALL', 'RANSOMWARE', 'PEELING_CHAIN', 'LAYERING', 'MIXING'].map(type => {
          const isActive = filterType === type;
          const count = alertList.filter(a => {
            if (type === 'ALL') return true;
            const pat = (a.predicted_pattern_type || '').toLowerCase();
            const filter = type.toLowerCase();
            if (filter === 'mixing') return pat.includes('mix') || pat.includes('coinjoin');
            if (filter === 'peeling_chain') return pat.includes('peel');
            if (filter === 'layering') return pat.includes('layer');
            if (filter === 'ransomware') return pat.includes('ransom');
            return pat === filter;
          }).length;

          return (
            <span
              key={type}
              onClick={() => setFilterType(type)}
              style={{
                cursor: 'pointer',
                padding: '3px 10px',
                borderRadius: '3px',
                background: isActive ? '#005520' : '#001a08',
                color: isActive ? '#00ff66' : '#94a3b8',
                border: `1px solid ${isActive ? '#00ff66' : '#003314'}`,
                fontWeight: isActive ? 'bold' : 'normal',
                userSelect: 'none',
                transition: 'all 0.1s ease',
              }}
            >
              {type} ({count})
            </span>
          );
        })}
      </div>

      {/* Alerts Body */}
      {filteredAlerts.length === 0 ? (
        <div style={{ color: '#94a3b8', textAlign: 'center', padding: '24px 0', fontSize: '13px' }}>
          Zero candidate alerts matching typology filter '{filterType}'.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div
            style={{
              backgroundColor: '#002211',
              color: '#00ff66',
              padding: '4px 10px',
              fontSize: '12px',
              fontWeight: 'bold',
              borderBottom: '1px solid #005520',
              marginBottom: '8px',
              letterSpacing: '1px',
              display: 'flex',
              justifyContent: 'space-between',
            }}
          >
            <span>▼ RANKED ILLICIT ALERTS ({filteredAlerts.length})</span>
            <span style={{ fontSize: '11px', color: '#94a3b8', letterSpacing: 'normal' }}>
              Sorted by risk_score DESC
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {filteredAlerts.map((alt, idx) => {
              const binConf = Number(alt.binary_confidence ?? 0);
              const typConf = Number(alt.typology_confidence ?? 0);
              const isCrit = alt.severity === 'CRITICAL';

              return (
                <div
                  key={alt.candidate_id || idx}
                  style={{
                    border: `1px solid ${isCrit ? '#991122' : '#004d20'}`,
                    padding: '10px 12px',
                    background: '#000c04',
                    borderRadius: '2px',
                  }}
                >
                  {/* Header line */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '6px', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span style={{ color: '#ffaa00', fontWeight: 'bold', fontSize: '13px' }}>
                        #{idx + 1}
                      </span>
                      <span
                        className="cmd-clickable"
                        onClick={() => onRunCommand(`alerts --detail ${alt.candidate_id}`)}
                        style={{ color: '#38bdf8', fontWeight: 'bold', fontFamily: 'monospace', fontSize: '13px' }}
                        title="Click to view deep SHAP evidence"
                      >
                        {alt.candidate_id}
                      </span>
                      {getPatternBadge(alt.predicted_pattern_type)}
                    </div>

                    <div style={{ color: '#00ff66', fontWeight: 800, fontSize: '12px', whiteSpace: 'nowrap' }}>
                      BIN/RISK <span style={{ color: binConf >= 0.7 ? '#ff3344' : '#ffaa00' }}>{(binConf * 100).toFixed(1)}%</span>
                      <span style={{ color: '#446644', margin: '0 4px' }}>·</span>
                      TYPO <span style={{ color: '#00ff66' }}>{(typConf * 100).toFixed(1)}%</span>
                    </div>
                  </div>

                  {/* Explanation */}
                  <div style={{ fontSize: '13px', color: '#f1f5f9', margin: '4px 0 6px 0', lineHeight: '1.45' }}>
                    {alt.explanation}
                  </div>

                  {/* Metadata & Actions */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px', fontSize: '12px', borderTop: '1px dashed #002b11', paddingTop: '6px' }}>
                    <div style={{ color: '#94a3b8' }}>
                      <span>Primary Wallet: </span>
                      <span className="cmd-clickable" onClick={() => onRunCommand(`inspect ${alt.primary_wallet}`)}>
                        {alt.primary_wallet}
                      </span>
                      <span style={{ margin: '0 6px', color: '#334433' }}>|</span>
                      <span>Scenario: </span>
                      <span className="cmd-clickable" onClick={() => onRunCommand(`graph ${alt.scenario_id}`)}>
                        {alt.scenario_id}
                      </span>
                      <span style={{ margin: '0 6px', color: '#334433' }}>|</span>
                      <span>{alt.member_txids?.length || 0} linked txns</span>
                      <span style={{ margin: '0 6px', color: '#334433' }}>|</span>
                      <span>Anomaly: {alt.anomaly_score?.toFixed(1) || '0.0'} ({alt.anomaly_label || 'LOW'})</span>
                    </div>

                    <div style={{ display: 'flex', gap: '8px' }}>
                      <span
                        className="cmd-tag"
                        onClick={() => onRunCommand(`alerts --detail ${alt.candidate_id}`)}
                        style={{ cursor: 'pointer', fontSize: '11px', color: '#38bdf8' }}
                      >
                        [🔍 SHAP Evidence]
                      </span>
                      <span
                        className="cmd-tag"
                        onClick={() => onRunCommand(`graph ${alt.scenario_id}`)}
                        style={{ cursor: 'pointer', fontSize: '11px', color: '#00ff66' }}
                      >
                        [🌐 3D Graph]
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
