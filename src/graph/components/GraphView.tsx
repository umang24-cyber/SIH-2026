import React, { useState, useEffect } from "react";
import GraphEngine from "./GraphEngine";
import { FORENSIC_SCENARIOS } from "../../data/forensicScenarios";
import { adaptScenarioToGraphData } from "../../adapters/forensicGraphAdapter";
import type { GraphMode, GraphData } from "../../types/graph";
import NodeDetails from "./NodeDetails";
import { api } from "../../services/api";

interface GraphViewProps {
  scenarioId?: string;
  onClose?: () => void;
}

export default function GraphView({
  scenarioId = "peel_001",
  onClose,
}: GraphViewProps) {
  const [mode, setMode] = useState<GraphMode>("OVERVIEW");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [graphData, setGraphData] = useState<GraphData>(() => {
    const sc = FORENSIC_SCENARIOS[scenarioId] || FORENSIC_SCENARIOS.peel_001;
    return adaptScenarioToGraphData(sc.nodes, sc.edges);
  });

  useEffect(() => {
    let isMounted = true;
    if (scenarioId) {
      api.getGraph(scenarioId)
        .then((res) => {
          if (isMounted && res && res.nodes && res.nodes.length > 0) {
            // Adapt backend scenario graph to GraphData
            const nodes = res.nodes.map((n: any, idx: number) => ({
              id: n.id,
              type: (n.type ? n.type.toUpperCase() : "WALLET") as any,
              label: n.label || n.id,
              x: (idx * 15) % 90 + 5,
              y: ((idx * 23) % 80) + 10,
              riskScore: n.properties?.is_licit_exchange ? 0.1 : (n.properties?.risk_score ?? n.properties?.taint_score ?? 0.75),
              clusterId: n.properties?.cluster_id || n.properties?.scenario_id || 'UNKNOWN',
              address: n.properties?.address,
              txid: n.properties?.txid ? String(n.properties.txid) : undefined,
              feeBtc: n.properties?.fee_btc,
              timestamp: n.properties?.timestamp,
              ipAddress: n.properties?.relay_ip,
              country: n.properties?.country_code,
              asn: n.properties?.asn,
            }));

            const edges = res.edges.map((e: any, idx: number) => ({
              id: e.id || `e_${idx}`,
              source: e.source,
              target: e.target,
              type: (e.type || "SENT") as any,
              amountBtc: e.amount_btc,
            }));

            setGraphData({ nodes, edges });
          }
        })
        .catch(() => {
          // Keep fallback scenario
        });
    }
    return () => {
      isMounted = false;
    };
  }, [scenarioId]);

  const selectedNode = graphData.nodes.find((node) => node.id === selectedNodeId) ?? null;

  return (
    <div
      className="graph-view"
      style={{
        width: "100%",
        minHeight: "600px",
        position: "relative",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: "10px",
          left: "10px",
          zIndex: 100,
          display: "flex",
          gap: "8px",
        }}
      >
        <button
          style={{ background: mode === "OVERVIEW" ? "#00ff66" : "#00220a", color: mode === "OVERVIEW" ? "#000" : "#00ff66", border: "1px solid #00ff66", padding: "4px 10px", cursor: "pointer", fontWeight: "bold" }}
          onClick={() => setMode("OVERVIEW")}
        >
          OVERVIEW
        </button>

        <button
          style={{ background: mode === "FLOW" ? "#00ff66" : "#00220a", color: mode === "FLOW" ? "#000" : "#00ff66", border: "1px solid #00ff66", padding: "4px 10px", cursor: "pointer", fontWeight: "bold" }}
          onClick={() => setMode("FLOW")}
        >
          FLOW
        </button>

        <button
          style={{ background: mode === "RISK" ? "#ff3333" : "#3b0808", color: mode === "RISK" ? "#fff" : "#ff3333", border: "1px solid #ff3333", padding: "4px 10px", cursor: "pointer", fontWeight: "bold" }}
          onClick={() => setMode("RISK")}
        >
          RISK MAP
        </button>

        <button
          style={{ background: mode === "CLUSTER" ? "#00ccff" : "#002b3d", color: mode === "CLUSTER" ? "#fff" : "#00ccff", border: "1px solid #00ccff", padding: "4px 10px", cursor: "pointer", fontWeight: "bold" }}
          onClick={() => setMode("CLUSTER")}
        >
          CLUSTERS
        </button>

        {onClose && (
          <button
            style={{ background: "#ff3344", color: "#fff", border: "none", padding: "4px 10px", cursor: "pointer", fontWeight: "bold" }}
            onClick={onClose}
          >
            EXIT
          </button>
        )}
      </div>

      <GraphEngine
        data={graphData}
        mode={mode}
        selectedNodeId={selectedNodeId}
        onSelectNode={(nodeId) => {
          setSelectedNodeId(nodeId);
        }}
      />
      <NodeDetails node={selectedNode} />
    </div>
  );
}