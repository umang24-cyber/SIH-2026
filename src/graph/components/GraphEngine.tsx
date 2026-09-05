import React from "react";
import type { GraphData, GraphMode } from "../../types/graph";
import GraphCanvas from "./GraphCanvas";

interface GraphEngineProps {
  data: GraphData;
  mode: GraphMode;
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string | null) => void;
}

export default function GraphEngine({
  data,
  mode,
  selectedNodeId,
  onSelectNode,
}: GraphEngineProps) {
  return (
    <div className="graph-engine">
      <GraphCanvas
  data={data}
  mode={mode}
  selectedNodeId={selectedNodeId}
  onSelectNode={onSelectNode}
/>
    </div>
  );
}