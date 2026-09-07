import React, { useState, useEffect } from 'react';
import { FORENSIC_SCENARIOS, GraphNode, ForensicAlert, ShapAttribution } from '../../data/forensicScenarios';
import { api, AlertSummary } from '../../services/api';
import { GraphCanvasBackdrop } from './GraphCanvasBackdrop';
import { AlertsSubwindow } from './AlertsSubwindow';
import { TelemetrySubwindow } from './TelemetrySubwindow';
import { ShapSubwindow } from './ShapSubwindow';
import { sound } from '../../audio/soundEngine';
import '../../styles/dashboard.css';
import GraphEngine from "../../graph/components/GraphEngine";
import { adaptScenarioToGraphData } from "../../adapters/forensicGraphAdapter";
import type { GraphMode } from "../../types/graph";

interface ForensicDashboardProps {
  onClose: () => void;
}

export const ForensicDashboard: React.FC<ForensicDashboardProps> = ({ onClose }) => {
  const [scenarioId, setScenarioId] = useState<string>('peel_001');
  const scenario = FORENSIC_SCENARIOS[scenarioId] || FORENSIC_SCENARIOS.peel_001;

  const [liveAlerts, setLiveAlerts] = useState<AlertSummary[]>([]);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [graphMode, setGraphMode] =
  useState<GraphMode>("OVERVIEW");
  const [selectedAlert, setSelectedAlert] = useState<ForensicAlert | AlertSummary | null>(scenario.alerts[0] || null);
  const [liveShapAttributions, setLiveShapAttributions] = useState<ShapAttribution[]>([]);

  // Fetch live backend alerts on mount
  useEffect(() => {
    api.getAlerts(0.5, 50)
      .then(res => {
        if (res && Array.isArray(res.alerts) && res.alerts.length > 0) {
          setLiveAlerts(res.alerts);
          setSelectedAlert(res.alerts[0]);
        }
      })
      .catch(() => {
        // Fallback to static scenario alerts if backend offline
      });
  }, []);

  // Fetch live TreeSHAP evidence whenever alert is selected
  useEffect(() => {
    if (selectedAlert && 'candidate_id' in selectedAlert && selectedAlert.candidate_id) {
      api.getAlertEvidence(selectedAlert.candidate_id)
        .then(ev => {
          const list = ev.ml_feature_attributions || ev.typology_shap_attributions || [];
          if (list.length > 0) {
            setLiveShapAttributions(list.map((it: any) => ({
              feature_name: it.feature_name,
              shap_value: typeof it.shap_value === 'number' ? it.shap_value : parseFloat(it.shap_value || '0'),
              direction: (it.direction && it.direction.includes('INCREASING')) || it.shap_value > 0 ? 'RISK_INCREASING' : 'RISK_DECREASING',
              value: String(it.value ?? 'N/A')
            })));
          }
        })
        .catch(() => {});
    }
  }, [selectedAlert]);

  // Master Window Collapse/Expand
  const [isWindowCollapsed, setIsWindowCollapsed] = useState<boolean>(false);

  // Subwindow visibility & minimized states
  const [showAlerts, setShowAlerts] = useState<boolean>(true);
  const [minAlerts, setMinAlerts] = useState<boolean>(false);

  const [showTelemetry, setShowTelemetry] = useState<boolean>(true);
  const [minTelemetry, setMinTelemetry] = useState<boolean>(false);

  const [showShap, setShowShap] = useState<boolean>(true);
  const [minShap, setMinShap] = useState<boolean>(false);

  // Reset node selection when scenario changes
  useEffect(() => {
    setSelectedNode(null);
    const availableAlerts = liveAlerts.length > 0 ? liveAlerts : scenario.alerts;
    setSelectedAlert(availableAlerts[0] || null);
  }, [scenarioId, liveAlerts]);

  // Keyboard shortcut listener: strictly ignore when user is typing in terminal input
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const activeTag = document.activeElement?.tagName.toLowerCase();
      // If user is currently typing in an input field, do not capture hotkeys
      if (activeTag === 'input' || activeTag === 'textarea') {
        return;
      }

      if (e.key === 'Escape') {
        sound.playEnterSuccess();
        onClose();
      } else if (e.key === 'a' || e.key === 'A') {
        setShowAlerts(prev => !prev);
        setMinAlerts(false);
        sound.playKeyClick();
      } else if (e.key === 'd' || e.key === 'D') {
        setShowTelemetry(prev => !prev);
        setMinTelemetry(false);
        sound.playKeyClick();
      } else if (e.key === 'x' || e.key === 'X') {
        setShowShap(prev => !prev);
        setMinShap(false);
        sound.playKeyClick();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleSelectScenario = (id: string) => {
    sound.playKeyClick();
    setScenarioId(id);
  };

  const handleSelectNode = (node: GraphNode) => {
    sound.playKeyClick();
    setSelectedNode(node);
    setShowTelemetry(true);
    setMinTelemetry(false);
  };

  const handleSelectAlert = (alert: any) => {
    sound.playKeyClick();
    setSelectedAlert(alert);
    const primaryWallet = scenario.nodes.find(n => n.id === alert.primary_wallet);
    if (primaryWallet) {
      setSelectedNode(primaryWallet);
    }
  };

  const walletCount = scenario.nodes.filter(n => n.type === 'Wallet').length;
  const txCount = scenario.nodes.filter(n => n.type === 'Transaction').length;
  const ipCount = scenario.nodes.filter(n => n.type === 'IP').length;
  const graphData = adaptScenarioToGraphData(
  scenario.nodes,
  scenario.edges
);

  return (
    <div className={`dashboard-embedded-window ${isWindowCollapsed ? 'minimized' : ''}`}>
      {/* 1. Master Top Forensic HUD Status Bar */}
      <div className="dashboard-topbar">
        <div className="topbar-left">
          <div className="hud-title">
            <span>[BITKAUN? INVESTIGATION]</span>
            <span style={{ color: '#ffffff' }}>FORENSIC GRAPH HUD</span>
          </div>

          {/* Scenario Selector Pills */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ color: '#94a3b8', fontSize: '11px' }}>SCENARIO:</span>
            {Object.keys(FORENSIC_SCENARIOS).map(id => (
              <span
                key={id}
                className={`hud-pill ${scenarioId === id ? 'active' : ''}`}
                onClick={() => handleSelectScenario(id)}
              >
                [{id}]
              </span>
            ))}
          </div>

          {/* Live Node Count Indicators */}
          <div style={{ display: 'flex', gap: '8px', fontSize: '11px', color: '#94a3b8' }}>
            <span>● {walletCount} Wallets</span>
            <span>■ {txCount} Transactions</span>
            <span>▲ {ipCount} Relay IPs</span>
          </div>
        </div>

        <div className="topbar-right">
          {/* Quick Subwindow Toggles */}
          <span
            className={`hud-pill ${showAlerts && !minAlerts ? 'active' : ''}`}
            onClick={() => {
              setShowAlerts(p => !p);
              setMinAlerts(false);
              sound.playKeyClick();
            }}
          >
            [A] Alerts
          </span>
          <span
            className={`hud-pill ${showTelemetry && !minTelemetry ? 'active' : ''}`}
            onClick={() => {
              setShowTelemetry(p => !p);
              setMinTelemetry(false);
              sound.playKeyClick();
            }}
          >
            [D] Dossier
          </span>
          <span
            className={`hud-pill ${showShap && !minShap ? 'active' : ''}`}
            onClick={() => {
              setShowShap(p => !p);
              setMinShap(false);
              sound.playKeyClick();
            }}
          >
            [X] SHAP
          </span>
          <button
  className={`hud-pill ${
    graphMode === "OVERVIEW" ? "active" : ""
  }`}
  onClick={() => {
    setGraphMode("OVERVIEW");
    sound.playKeyClick();
  }}
>
  OVERVIEW
</button>

<button
  className={`hud-pill ${
    graphMode === "FLOW" ? "active" : ""
  }`}
  onClick={() => {
    setGraphMode("FLOW");
    sound.playKeyClick();
  }}
>
  FLOW
</button>
<button
  className={`hud-pill ${
    graphMode === "RISK" ? "active" : ""
  }`}
  onClick={() => {
    setGraphMode("RISK");
    sound.playKeyClick();
  }}
>
  RISK
</button>
<button
  className={`hud-pill ${
    graphMode === "CLUSTER"
      ? "active"
      : ""
  }`}
  onClick={() => {
    setGraphMode("CLUSTER");
    sound.playKeyClick();
  }}
>
  CLUSTER
</button>
          {/* Window Collapse / Expand */}
          <button
            className="hud-pill"
            onClick={() => setIsWindowCollapsed(p => !p)}
            title={isWindowCollapsed ? 'Expand graph window' : 'Collapse graph window'}
          >
            {isWindowCollapsed ? '[▲ EXPAND]' : '[— COLLAPSE]'}
          </button>

          {/* Close / Dismiss embedded window */}
          <button className="close-btn" onClick={onClose} title="Close Graph Window">
            [x CLOSE]
          </button>
        </div>
      </div>

      {/* 2. Central Full-Viewport Graph Stage + Overlay Subwindows (Hidden when collapsed) */}
      {!isWindowCollapsed && (
        <div className="dashboard-stage">
          {/* Fullscreen Link-Analysis Graph Canvas Backdrop */}
          <GraphEngine
  data={graphData}
  mode={graphMode}
  selectedNodeId={selectedNode?.id || null}
  onSelectNode={(nodeId) => {
    if (nodeId === null) {
      setSelectedNode(null);
      return;
    }

    const node = scenario.nodes.find(
      (currentNode) => currentNode.id === nodeId
    );

    if (node) {
      handleSelectNode(node);
    }
  }}
/>

          {/* Subwindow 1: Ranked Alerts Inbox (Top-Left) */}
          {showAlerts && !minAlerts && (
            <AlertsSubwindow
              alerts={liveAlerts.length > 0 ? liveAlerts : scenario.alerts}
              selectedAlertId={selectedAlert?.candidate_id || null}
              onSelectAlert={handleSelectAlert}
              onMinimize={() => setMinAlerts(true)}
              onClose={() => setShowAlerts(false)}
              style={{ top: '16px', left: '20px' }}
            />
          )}

          {/* Subwindow 2: Dual-Layer Telemetry Dossier (Top-Right) */}
          {showTelemetry && !minTelemetry && (
            <TelemetrySubwindow
  selectedNode={selectedNode}
  scenario={scenario}
  graphData={graphData}
  onMinimize={() => setMinTelemetry(true)}
  onClose={() => setShowTelemetry(false)}
  style={{ top: '16px', right: '20px' }}
/>
          )}

          {/* Subwindow 3: Explainable AI SHAP Attribution HUD (Bottom-Left) */}
          {showShap && !minShap && (
            <ShapSubwindow
              attributions={liveShapAttributions.length > 0 ? liveShapAttributions : scenario.shap_attributions}
              scenarioName={selectedAlert?.candidate_id || scenario.name}
              onMinimize={() => setMinShap(true)}
              onClose={() => setShowShap(false)}
              style={{ bottom: '16px', left: '20px' }}
            />
          )}
        </div>
      )}

      {/* 3. Bottom Dock & Minimized Windows Bar */}
      {!isWindowCollapsed && (
        <div className="dashboard-dock">
          <div className="dock-pills">
            <span style={{ color: '#94a3b8', marginRight: '4px' }}>DOCK:</span>
            {(!showAlerts || minAlerts) && (
              <span
                className="dock-pill"
                onClick={() => {
                  setShowAlerts(true);
                  setMinAlerts(false);
                  sound.playKeyClick();
                }}
              >
                + WIN_01: ALERTS_QUEUE
              </span>
            )}
            {(!showTelemetry || minTelemetry) && (
              <span
                className="dock-pill"
                onClick={() => {
                  setShowTelemetry(true);
                  setMinTelemetry(false);
                  sound.playKeyClick();
                }}
              >
                + WIN_02: DUAL_TELEMETRY
              </span>
            )}
            {(!showShap || minShap) && (
              <span
                className="dock-pill"
                onClick={() => {
                  setShowShap(true);
                  setMinShap(false);
                  sound.playKeyClick();
                }}
              >
                + WIN_03: SHAP_EXPLAINER
              </span>
            )}
            {showAlerts && !minAlerts && showTelemetry && !minTelemetry && showShap && !minShap && (
              <span style={{ color: '#94a3b8' }}>ALL SUBWINDOWS DOCKED TO STAGE</span>
            )}
          </div>

          <div style={{ color: '#94a3b8' }}>
            <span>STATUS: <strong style={{ color: '#00ff66' }}>ONLINE</strong> | NTRO-PS146 SPECIFICATION SYNCED</span>
          </div>
        </div>
      )}
    </div>
  );
};
