import React from 'react';
import { ShapAttribution } from '../../data/forensicScenarios';

interface ShapSubwindowProps {
  attributions: ShapAttribution[];
  scenarioName: string;
  onMinimize: () => void;
  onClose: () => void;
  style?: React.CSSProperties;
}

export const ShapSubwindow: React.FC<ShapSubwindowProps> = ({
  attributions,
  scenarioName,
  onMinimize,
  onClose,
  style
}) => {
  return (
    <div
      className="tui-subwindow"
      style={{
        width: '580px',
        maxHeight: '340px',
        ...style
      }}
    >
      {/* Retro Window Header */}
      <div className="tui-window-titlebar">
        <span>┌─[ WIN_03: XAI_SHAP_REASONING.explainer ]</span>
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
        <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '10px' }}>
          MODEL ATTRIBUTION REASONING FOR: <strong style={{ color: '#00ff66' }}>{scenarioName}</strong>
        </div>

        {attributions.map((attr, idx) => {
          const isRiskUp = attr.direction === 'RISK_INCREASING';
          const absVal = Math.abs(attr.shap_value);
          const percent = Math.min(100, Math.round(absVal * 220));

          return (
            <div key={idx} className="shap-item">
              <div className="shap-header">
                <span style={{ color: '#ffffff', fontWeight: 700, fontSize: '13px' }}>
                  {attr.feature_name}
                </span>
                <span style={{ color: isRiskUp ? '#00ff66' : '#94a3b8', fontWeight: 700, fontSize: '12px' }}>
                  Value: {attr.value} | SHAP: {attr.shap_value > 0 ? `+${attr.shap_value.toFixed(3)}` : attr.shap_value.toFixed(3)}
                </span>
              </div>

              <div className="shap-bar-track">
                <div
                  className={`shap-bar-fill ${isRiskUp ? 'shap-fill-risk-up' : 'shap-fill-risk-down'}`}
                  style={{ width: `${percent}%` }}
                />
              </div>

              <div style={{ fontSize: '11px', color: isRiskUp ? '#4ade80' : '#64748b', marginTop: '3px', fontWeight: 600 }}>
                {isRiskUp ? '▲ RISK INCREASING (Directly influenced illicit typology classification)' : '▼ RISK DECREASING (Matches standard baseline pattern)'}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
