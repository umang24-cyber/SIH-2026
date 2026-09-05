import React, { useState } from "react";

import GraphEngine from "./GraphEngine";

import { FORENSIC_SCENARIOS } from "../../data/forensicScenarios";

import { adaptScenarioToGraphData } from "../../adapters/forensicGraphAdapter";

import type { GraphMode } from "../../types/graph";
import NodeDetails from "./NodeDetails";



interface GraphViewProps {
  onClose?: () => void;
}

export default function GraphView({
  onClose,
}: GraphViewProps) {
  const [mode, setMode] =
  useState<GraphMode>("OVERVIEW");

  const [selectedNodeId, setSelectedNodeId] =
    useState<string | null>(null);

  const scenario =
    FORENSIC_SCENARIOS.peel_001;

  const graphData =
    adaptScenarioToGraphData(
      scenario.nodes,
      scenario.edges
    );
 const selectedNode =
  graphData.nodes.find(
    (node) => node.id === selectedNodeId
  ) ?? null;

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
    onClick={() => setMode("OVERVIEW")}
  >
    OVERVIEW
  </button>

  <button
    onClick={() => setMode("FLOW")}
  >
    FLOW
  </button>
</div>

    <GraphEngine
      data={graphData}
      mode={mode}
      selectedNodeId={selectedNodeId}
      onSelectNode={(nodeId) => {
        setSelectedNodeId(nodeId);
      }}
    />
    <NodeDetails
  node={selectedNode}
/>

    {/* existing EXIT button stays here */}
  </div>
);
}