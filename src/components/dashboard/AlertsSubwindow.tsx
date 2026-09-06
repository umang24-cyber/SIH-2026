import React, { useState } from 'react';
import { ForensicAlert } from '../../data/forensicScenarios';

interface AlertsSubwindowProps {
  alerts: ForensicAlert[];
  selectedAlertId: string | null;
  onSelectAlert: (alert: ForensicAlert) => void;
  onMinimize: () => void;
  onClose: () => void;
  style?: React.CSSProperties;
}

export const AlertsSubwindow: React.FC<AlertsSubwindowProps> = ({
  alerts,
  selectedAlertId,
  onSelectAlert,
  onMinimize,
  onClose,
  style
}) => {
  const [filterType, setFilterType] = useState<string>('ALL');

  const filteredAlerts = alerts.filter(a => {
    if (filterType === 'ALL') return true;
    return a.predicted_pattern_type.toLowerCase() === filterType.toLowerCase();
  });

  return (
    <div
      className="tui-subwindow"
      style={{
        width: '400px',
        maxHeight: '460px',
        ...style
      }}
    >
      {/* Retro Window Header */}
      <div className="tui-window-titlebar">
        <span>┌─[ WIN_01: ALERTS_QUEUE ]</span>
        <div className="window-ctrls">
          <span className="window-ctrl-btn" onClick={onMinimize} title="Minimize">
            [—]
          </span>
          <span className="window-ctrl-btn" onClick={onClose} title="Close">
            [x]
          </span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '6px',
          padding: '8px 12px',
          borderBottom: '1px solid #005520',
          fontSize: '12px',
          flexWrap: 'wrap'
        }}
      >
        {['ALL', 'RANSOMWARE', 'PEELING_CHAIN', 'LAYERING', 'MIXING'].map(type => (
          <span
            key={type}
            className={`hud-pill ${filterType === type ? 'active' : ''}`}
            onClick={() => setFilterType(type)}
            style={{ fontSize: '11px' }}
          >
            {type}
          </span>
        ))}
      </div>

      {/* Alerts Body */}
      <div className="tui-window-body">
        {filteredAlerts.length === 0 ? (
          <div style={{ color: '#94a3b8', textAlign: 'center', padding: '24px 0', fontSize: '13px' }}>
            No alerts matching filter.
          </div>
        ) : (
          ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(severityLevel => {
            const groupAlerts = filteredAlerts.filter(a => a.severity === severityLevel);
            if (groupAlerts.length === 0) return null;

            return (
              <div key={severityLevel} style={{ marginBottom: '16px' }}>
                {/* Divider Header */}
                <div style={{
                  backgroundColor: severityLevel === 'CRITICAL' ? '#330000' : '#002211',
                  color: severityLevel === 'CRITICAL' ? '#ff3344' : '#00ff66',
                  padding: '4px 8px',
                  fontSize: '11px',
                  fontWeight: 'bold',
                  borderBottom: `1px solid ${severityLevel === 'CRITICAL' ? '#ff3344' : '#005520'}`,
                  marginBottom: '8px',
                  letterSpacing: '1px'
                }}>
                  ▼ {severityLevel} THREATS ({groupAlerts.length})
                </div>

                {groupAlerts.map(alert => {
                  const isSelected = alert.candidate_id === selectedAlertId;
                  const severityClass =
                    alert.severity === 'CRITICAL'
                      ? 'severity-critical'
                      : alert.severity === 'HIGH'
                      ? 'severity-high'
                      : 'severity-medium';

                  return (
                    <div
                      key={alert.candidate_id}
                      className={`alert-card-item ${isSelected ? 'selected' : ''}`}
                      onClick={() => onSelectAlert(alert)}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '4px', marginBottom: '6px' }}>
                        <span className={`severity-tag ${severityClass}`}>
                          {alert.severity} • {alert.predicted_pattern_type.toUpperCase()}
                        </span>
                        <span style={{ color: '#00ff66', fontWeight: 800, fontSize: '12px', whiteSpace: 'nowrap' }}>
                          BIN {(alert.binary_confidence * 100).toFixed(1)}% · TYPO {(alert.typology_confidence * 100).toFixed(1)}%
                        </span>
                      </div>

                      <div style={{ fontSize: '13px', color: '#f8fafc', marginBottom: '6px', lineHeight: '1.45' }}>
                        {alert.explanation}
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#94a3b8' }}>
                        <span>Wallet: <strong style={{ color: '#ffffff' }}>{alert.primary_wallet.slice(0, 12)}...</strong></span>
                        <span>{alert.member_txids.length} linked txns</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
