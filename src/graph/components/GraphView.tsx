import React, { useState, useEffect } from "react";
import GraphEngine from "./GraphEngine";
import type { GraphMode, GraphData } from "../../types/graph";
import NodeDetails from "./NodeDetails";
import { api, type IngestScenarioAnalysis } from "../../services/api";
import { CliSpinner } from "../../components/CliSpinner";

interface GraphViewProps {
  scenarioId?: string;
  onClose?: () => void;
}

export default function GraphView({
  scenarioId = "normal_00002",
  onClose,
}: GraphViewProps) {
  const [currentScenario, setCurrentScenario] = useState<string>(scenarioId || "normal_00002");
  const [inputScenario, setInputScenario] = useState<string>(scenarioId || "normal_00002");
  const [mode, setMode] = useState<GraphMode>("OVERVIEW");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [mlAnalysis, setMlAnalysis] = useState<IngestScenarioAnalysis | null>(null);

  // Suggested scenarios available in the ledger
  const quickScenarios = ["normal_00002", "ransomware_03287", "peeling_chain_04651", "mixing_05246", "normal_02462"];

  const loadScenario = (scId: string) => {
    setIsLoading(true);
    setErrorMsg(null);
    setSelectedNodeId(null);
    setMlAnalysis(null);

    const unavailableAnalysis: IngestScenarioAnalysis = {
      scenario_id: scId,
      transaction_count: 0,
      analysis_status: "UNAVAILABLE",
      analysis_message: "ML analysis could not be retrieved for this scenario.",
      feature_count: 46,
      score_scope: "SCENARIO",
      sample_size_warning: null,
      typology_explanation: "",
      anomaly_message: "",
      top_shap_attributions: [],
      typology_shap_attributions: [],
    };

    Promise.all([
      api.getGraph(scId),
      api.getIngestScenarioAnalysis(scId).catch(() => unavailableAnalysis),
    ])
      .then(([res, analysis]) => {
        if (res && res.nodes && res.nodes.length > 0) {
          setMlAnalysis(analysis);
          const hasModelRisk = analysis.analysis_status === "AVAILABLE"
            && Number.isFinite(Number(analysis.risk_score));
          const modelRisk = hasModelRisk ? Number(analysis.risk_score) : undefined;

          // Use the cached scenario-level backend result.  No scenario-name
          // or typology heuristic is allowed to stand in for ML output.
          const nodes: GraphData['nodes'] = res.nodes.map((n: any) => {
            const rawType = (n.type ? n.type.toUpperCase() : "WALLET");
            const props = n.properties || {};
            const risk = modelRisk;
            const mlFields = {
              riskScore: risk,
              mlAnalysisStatus: analysis.analysis_status,
              mlAnalysisMessage: [analysis.analysis_message, analysis.sample_size_warning].filter(Boolean).join(" "),
              scoreScope: "SCENARIO" as const,
              isIllicit: analysis.is_illicit ?? undefined,
              binaryConfidence: analysis.binary_confidence ?? undefined,
              typologyConfidence: analysis.typology_confidence ?? undefined,
              predictedTypology: analysis.predicted_typology ?? undefined,
              anomalyScore: analysis.anomaly_score ?? undefined,
              anomalyLabel: analysis.anomaly_label ?? undefined,
            };

            if (rawType === "TRANSACTION") {
              return {
                id: n.id,
                type: "TRANSACTION" as const,
                label: n.label || `TX_${props.txid || n.id}`,
                txid: String(props.txid || n.id),
                amountBtc: props.amount_btc,
                feeBtc: props.fee_btc,
                timestamp: props.timestamp,
                clusterId: props.cluster_id,
                ...mlFields,
              };
            } else if (rawType === "IP") {
              return {
                id: n.id,
                type: "IP" as const,
                label: n.label || props.relay_ip || n.id,
                ipAddress: props.relay_ip || n.id,
                asn: props.asn,
                country: props.country_code,
                isp: props.isp,
                clusterId: props.cluster_id,
                ...mlFields,
              };
            } else {
              return {
                id: n.id,
                type: "WALLET" as const,
                label: n.label || props.address || n.id,
                address: props.address || n.id,
                clusterId: props.cluster_id,
                ...mlFields,
              };
            }
          });

          const edges = res.edges.map((e: any, idx: number) => ({
            id: e.id || `e_${idx}`,
            source: e.source,
            target: e.target,
            type: (e.type || "SENT") as any,
            amountBtc: e.properties?.amount_btc ?? e.amount_btc,
          }));

          setGraphData({ nodes, edges });
          setCurrentScenario(scId);
        } else {
          setErrorMsg(`Scenario '${scId}' returned zero nodes. Intended feature: "Dynamic scenario lookup across all loaded clusters"`);
          setGraphData({ nodes: [], edges: [] });
        }
      })
      .catch((err) => {
        setErrorMsg(`Scenario '${scId}' not found in live blockchain store (${err.message}). Intended feature: "Dynamic scenario lookup across all loaded clusters"`);
        setGraphData({ nodes: [], edges: [] });
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  useEffect(() => {
    loadScenario(currentScenario);
  }, [currentScenario]);

  const selectedNode = graphData.nodes.find((node) => node.id === selectedNodeId) ?? null;

  return (
    <div
      className="graph-view"
      style={{
        width: "100%",
        position: "relative",
        background: "#000803",
        border: "1px solid #005520",
        borderRadius: "4px",
      }}
    >
      {/* Top Navigation & Scenario Switcher Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          padding: "10px 14px",
          background: "rgba(0, 20, 8, 0.95)",
          borderBottom: "1px solid #005520",
          gap: "8px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ color: "#33ff88", fontWeight: "bold", fontSize: "14px" }}>
            ACTIVE SCENARIO:
          </span>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (inputScenario.trim()) {
                setCurrentScenario(inputScenario.trim());
              }
            }}
            style={{ display: "flex", gap: "6px" }}
          >
            <input
              type="text"
              value={inputScenario}
              onChange={(e) => setInputScenario(e.target.value)}
              placeholder="e.g. licit_00001, ransom_0001"
              style={{
                background: "#001406",
                border: "1px solid #00aa44",
                color: "#aaffaa",
                padding: "3px 8px",
                fontFamily: "monospace",
                fontSize: "13px",
                borderRadius: "3px",
              }}
            />
            <button
              type="submit"
              style={{
                background: "#00ff66",
                color: "#000",
                border: "none",
                padding: "3px 10px",
                fontWeight: "bold",
                cursor: "pointer",
                borderRadius: "3px",
              }}
            >
              LOAD
            </button>
          </form>

          {/* Quick Scenario Buttons */}
          <div style={{ display: "flex", gap: "4px", marginLeft: "6px" }}>
            {quickScenarios.map((sc) => (
              <button
                key={sc}
                onClick={() => {
                  setInputScenario(sc);
                  setCurrentScenario(sc);
                }}
                style={{
                  background: currentScenario === sc ? "#00aa44" : "#00240d",
                  color: currentScenario === sc ? "#fff" : "#33ff88",
                  border: "1px solid #005520",
                  padding: "2px 6px",
                  fontSize: "11px",
                  fontFamily: "monospace",
                  cursor: "pointer",
                  borderRadius: "2px",
                }}
              >
                {sc}
              </button>
            ))}
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          {mlAnalysis && (
            <span
              style={{
                color: mlAnalysis.analysis_status === "AVAILABLE" ? "#33ff88" : "#ffaa33",
                fontSize: "12px",
                fontFamily: "monospace",
              }}
            >
              ML: SCENARIO {mlAnalysis.analysis_status}
              {mlAnalysis.analysis_status === "AVAILABLE" && mlAnalysis.risk_score !== null && mlAnalysis.risk_score !== undefined
                ? ` · RISK ${(mlAnalysis.risk_score * 100).toFixed(2)}%`
                : ""}
            </span>
          )}
          <span style={{ color: "#00aa44", fontSize: "12px", fontFamily: "monospace" }}>
            {graphData.nodes.length} Nodes · {graphData.edges.length} Edges
          </span>
          {onClose && (
            <button
              onClick={onClose}
              style={{
                background: "#ff3344",
                color: "#fff",
                border: "none",
                padding: "4px 10px",
                cursor: "pointer",
                fontWeight: "bold",
                fontSize: "12px",
                borderRadius: "3px",
              }}
            >
              CLOSE
            </button>
          )}
        </div>
      </div>

      {/* Main Canvas Area */}
      {isLoading ? (
        <div style={{ height: "540px", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", color: "#33ff88" }}>
          <CliSpinner
            label={`RETRIEVING FORENSIC SUBGRAPH FOR SCENARIO [${currentScenario}]...`}
            style={{ fontSize: "16px" }}
          />
          <div style={{ color: "#00aa44", fontSize: "12px", marginTop: "10px", fontFamily: "monospace" }}>
            Calculating UTXO fund flows, address clusters &amp; network propagation telemetry...
          </div>
        </div>
      ) : errorMsg ? (
        <div style={{ height: "640px", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", color: "#ff3344", padding: "20px", textAlign: "center" }}>
          <div style={{ fontSize: "16px", fontWeight: "bold", marginBottom: "8px" }}>
            [GRAPH EXTRACTION NOTICE]
          </div>
          <div style={{ maxWidth: "600px", color: "#ff8899", fontSize: "14px", lineHeight: "1.5" }}>
            {errorMsg}
          </div>
          <button
            onClick={() => {
              setInputScenario("normal_00002");
              setCurrentScenario("normal_00002");
            }}
            style={{
              marginTop: "16px",
              background: "#00ff66",
              color: "#000",
              border: "none",
              padding: "6px 14px",
              fontWeight: "bold",
              cursor: "pointer",
              borderRadius: "3px",
            }}
          >
            Load Default Scenario (normal_00002)
          </button>
        </div>
      ) : (
        <>
          <GraphEngine
            data={graphData}
            mode={mode}
            selectedNodeId={selectedNodeId}
            onSelectNode={(nodeId) => setSelectedNodeId(nodeId)}
          />
          <NodeDetails node={selectedNode} />
        </>
      )}
    </div>
  );
}
