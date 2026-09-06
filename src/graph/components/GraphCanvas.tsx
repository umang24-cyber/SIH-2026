import React, { useState } from "react";
import type {
  GraphData,
  GraphNode,
  GraphEdge,
  GraphMode,
} from "../../types/graph";

interface GraphCanvasProps {
  data: GraphData;
  mode: GraphMode;
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string | null) => void;
}

function getDynamicNodePositions(
  nodes: GraphNode[],
  edges: GraphEdge[]
) {
  const outgoingEdges = new Map<string, string[]>();
  const incomingCount = new Map<string, number>();
  const layers = new Map<string, number>();

  nodes.forEach((node) => {
    outgoingEdges.set(node.id, []);
    incomingCount.set(node.id, 0);
  });

  edges.forEach((edge) => {
    const outgoing = outgoingEdges.get(edge.source);

    if (outgoing) {
      outgoing.push(edge.target);
    }

    incomingCount.set(
      edge.target,
      (incomingCount.get(edge.target) ?? 0) + 1
    );
  });

  const queue: string[] = [];

  nodes.forEach((node) => {
    if ((incomingCount.get(node.id) ?? 0) === 0) {
      queue.push(node.id);
      layers.set(node.id, 0);
    }
  });

  let queueIndex = 0;

  while (queueIndex < queue.length) {
    const currentNodeId = queue[queueIndex];
    queueIndex++;

    const currentLayer =
      layers.get(currentNodeId) ?? 0;

    const connectedNodes =
      outgoingEdges.get(currentNodeId) ?? [];

    connectedNodes.forEach((targetId) => {
      const nextLayer = currentLayer + 1;

      const existingLayer =
        layers.get(targetId);

      if (
        existingLayer === undefined ||
        nextLayer > existingLayer
      ) {
        layers.set(targetId, nextLayer);
      }

      const remainingIncoming =
        (incomingCount.get(targetId) ?? 0) - 1;

      incomingCount.set(
        targetId,
        remainingIncoming
      );

      if (remainingIncoming === 0) {
        queue.push(targetId);
      }
    });
  }

  let highestLayer = Math.max(
    ...Array.from(layers.values()),
    0
  );

  nodes.forEach((node) => {
    if (!layers.has(node.id)) {
      highestLayer++;

      layers.set(
        node.id,
        highestLayer
      );
    }
  });

  const nodesByLayer = new Map<
    number,
    GraphNode[]
  >();

  nodes.forEach((node) => {
    const layer =
      layers.get(node.id) ?? 0;

    const layerNodes =
      nodesByLayer.get(layer) ?? [];

    layerNodes.push(node);

    nodesByLayer.set(
      layer,
      layerNodes
    );
  });

  const positions = new Map<
    string,
    { x: number; y: number }
  >();

  const horizontalSpacing = 220;
  const verticalSpacing = 150;

  nodesByLayer.forEach(
    (layerNodes, layer) => {
      const x =
        160 +
        layer * horizontalSpacing;

      const totalHeight =
        (layerNodes.length - 1) *
        verticalSpacing;

      const startY =
        350 -
        totalHeight / 2;

      layerNodes.forEach(
        (node, index) => {
          positions.set(node.id, {
            x,
            y:
              startY +
              index * verticalSpacing,
          });
        }
      );
    }
  );

  return positions;
}

function getNodeStyle(node: GraphNode) {
  switch (node.type) {
    case "WALLET":
      return {
        fill: "#062a18",
        stroke: "#00ff66",
        label: "W",
      };

    case "TRANSACTION":
      return {
        fill: "#2a1a05",
        stroke: "#ff9900",
        label: "TX",
      };

    case "IP":
      return {
        fill: "#1d0a33",
        stroke: "#bb66ff",
        label: "IP",
      };
  }
}

function getNodeRadius(node: GraphNode) {
  switch (node.type) {
    case "WALLET":
      return 28;

    case "TRANSACTION":
      return 32;

    case "IP":
      return 36;
  }
}

function getEdgeCoordinates(
  sourceNode: GraphNode,
  targetNode: GraphNode,
  sourcePosition: { x: number; y: number },
  targetPosition: { x: number; y: number }
) {
  const dx = targetPosition.x - sourcePosition.x;
  const dy = targetPosition.y - sourcePosition.y;

  const distance = Math.sqrt(
    dx * dx + dy * dy
  );

  if (distance === 0) {
    return {
      x1: sourcePosition.x,
      y1: sourcePosition.y,
      x2: targetPosition.x,
      y2: targetPosition.y,
    };
  }

  const unitX = dx / distance;
  const unitY = dy / distance;

  const sourceOffset =
    getNodeRadius(sourceNode) + 4;

  const targetOffset =
    getNodeRadius(targetNode) + 14;

  return {
    x1:
      sourcePosition.x +
      unitX * sourceOffset,

    y1:
      sourcePosition.y +
      unitY * sourceOffset,

    x2:
      targetPosition.x -
      unitX * targetOffset,

    y2:
      targetPosition.y -
      unitY * targetOffset,
  };
}
function getRiskColor(
  node: GraphNode,
  isRiskMode: boolean
) {
  if (!isRiskMode) {
    return null;
  }

  const riskScore = node.riskScore ?? 0;

  if (riskScore >= 0.8) {
    return {
      fill: "#3b0808",
      stroke: "#ff3333",
    };
  }

  if (riskScore >= 0.5) {
    return {
      fill: "#3a2205",
      stroke: "#ff9900",
    };
  }

  return {
    fill: "#062a18",
    stroke: "#00ff66",
  };
}

function getClusterColor(
  clusterId: string | undefined,
  isClusterMode: boolean
) {
  if (!isClusterMode) {
    return null;
  }
  
  if (!clusterId || clusterId === 'UNKNOWN') {
    return {
      fill: "#062a18",
      stroke: "#00ff66",
    };
  }

  // Simple string hash function
  let hash = 0;
  for (let i = 0; i < clusterId.length; i++) {
    hash = clusterId.charCodeAt(i) + ((hash << 5) - hash);
  }

  // Generate distinct HSL colors based on hash
  const h = Math.abs(hash) % 360;
  // Keep saturation high and lightness low for dark mode theme
  const fillL = 15;
  const strokeL = 50;
  
  return {
    fill: `hsl(${h}, 80%, ${fillL}%)`,
    stroke: `hsl(${h}, 90%, ${strokeL}%)`,
  };
}

export default function GraphCanvas({
  data,
  mode,
  selectedNodeId,
  onSelectNode,
}: GraphCanvasProps) {
    
    const [hoveredNodeId, setHoveredNodeId] =
  useState<string | null>(null);
const isFlowMode = mode === "FLOW";
const isRiskMode = mode === "RISK";
const isClusterMode = mode === "CLUSTER";

const visibleNodes =
  mode === "OVERVIEW"
    ? data.nodes
    : data.nodes;

const visibleEdges =
  mode === "OVERVIEW"
    ? data.edges
    : data.edges;

const nodePositions =
  getDynamicNodePositions(
    visibleNodes,
    visibleEdges
  );

const positions = Array.from(
  nodePositions.values()
);

const connectedNodeIds = new Set<string>();

if (selectedNodeId) {
  visibleEdges.forEach((edge) => {
    if (edge.source === selectedNodeId) {
      connectedNodeIds.add(edge.target);
    }

    if (edge.target === selectedNodeId) {
      connectedNodeIds.add(edge.source);
    }
  });
}

  const padding = 180;
  const labelSpace = 80;

  const minX =
    Math.min(
      ...positions.map(
        (position) => position.x
      )
    ) - padding;

  const maxX =
    Math.max(
      ...positions.map(
        (position) => position.x
      )
    ) + padding;

  const minY =
    Math.min(
      ...positions.map(
        (position) => position.y
      )
    ) - padding;

  const maxY =
    Math.max(
      ...positions.map(
        (position) => position.y
      )
    ) +
    padding +
    labelSpace;

  const graphWidth = maxX - minX;

  const graphHeight = maxY - minY;

  return (
    <div
      className="graph-canvas"
      style={{
        width: "100%",
        height: "700px",
        overflow: "hidden",
      }}
    >
      <svg
        viewBox={`${minX} ${minY} ${graphWidth} ${graphHeight}`}
        preserveAspectRatio="xMidYMid meet"
        width="100%"
        height="100%"
        style={{
          width: "100%",
          height: "100%",
          display: "block",
        }}
      >
        <defs>
          <marker
            id="arrow-green"
            markerWidth="12"
            markerHeight="12"
            refX="10"
            refY="6"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path
              d="M0,0 L12,6 L0,12 z"
              fill="#00cc66"
            />
          </marker>

          <marker
            id="arrow-purple"
            markerWidth="12"
            markerHeight="12"
            refX="10"
            refY="6"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path
              d="M0,0 L12,6 L0,12 z"
              fill="#bb66ff"
            />
          </marker>
        </defs>

        {data.edges.map((edge) => {
          const sourcePosition =
            nodePositions.get(edge.source);

          const targetPosition =
            nodePositions.get(edge.target);

          const sourceNode =
            data.nodes.find(
              (node) =>
                node.id === edge.source
            );

          const targetNode =
            data.nodes.find(
              (node) =>
                node.id === edge.target
            );

          if (
            !sourcePosition ||
            !targetPosition ||
            !sourceNode ||
            !targetNode
          ) {
            return null;
          }

          const coordinates =
            getEdgeCoordinates(
              sourceNode,
              targetNode,
              sourcePosition,
              targetPosition
            );

          const isBroadcast =
            edge.type === "BROADCAST";

            const isConnectedToSelectedNode =
  selectedNodeId !== null &&
  (
    edge.source === selectedNodeId ||
    edge.target === selectedNodeId
  );
          const isConnectedToHoveredNode =
  hoveredNodeId !== null &&
  (
    edge.source === hoveredNodeId ||
    edge.target === hoveredNodeId
  );

          return (
            <line
              key={edge.id}
              x1={coordinates.x1}
              y1={coordinates.y1}
              x2={coordinates.x2}
              y2={coordinates.y2}
              stroke={
  isBroadcast
    ? "#bb66ff"
    : isFlowMode
      ? "#00ff88"
      : "#00cc66"
}

strokeWidth={
  isConnectedToSelectedNode
    ? "4"
    : isConnectedToHoveredNode
      ? "3.5"
      : isFlowMode
        ? "3"
        : "2"
}

opacity={
  selectedNodeId !== null
    ? isConnectedToSelectedNode
      ? "1"
      : "0.15"
    : hoveredNodeId !== null
      ? isConnectedToHoveredNode
        ? "1"
        : "0.15"
      : isFlowMode
        ? "0.95"
        : "0.7"
}

strokeDasharray={
  isBroadcast
    ? "6 6"
    : undefined
}

              markerEnd={
                isBroadcast
                  ? "url(#arrow-purple)"
                  : "url(#arrow-green)"
              }
            />
          );
        })}

        {data.nodes.map((node) => {
          const position =
            nodePositions.get(node.id);
          const isSelected =
  selectedNodeId === node.id;
          const isConnected =
  connectedNodeIds.has(node.id);

          if (!position) {
            return null;
          }

          const style = getNodeStyle(node);

const riskStyle = getRiskColor(
  node,
  isRiskMode
);

const clusterStyle = getClusterColor(
  node.clusterId,
  isClusterMode
);

const nodeFill =
  riskStyle?.fill ??
  clusterStyle?.fill ??
  style.fill;

const nodeStroke =
  riskStyle?.stroke ??
  clusterStyle?.stroke ??
  style.stroke;
          const isHovered =
  hoveredNodeId === node.id;

          return (
            <g
  key={node.id}
  transform={`translate(${position.x}, ${position.y}) scale(${
    isHovered || isSelected ? 1.12 : 1
  })`}
  onMouseEnter={() => setHoveredNodeId(node.id)}
  onMouseLeave={() => setHoveredNodeId(null)}
  onClick={() =>
  onSelectNode(
    isSelected ? null : node.id
  )
}
  style={{
  cursor: "pointer",

  opacity:
    selectedNodeId !== null
      ? isSelected || isConnected
        ? 1
        : 0.25
      : hoveredNodeId !== null
        ? isHovered
          ? 1
          : 0.4
        : 1,

  transition: "opacity 0.2s ease",
}}
  
>
    {isSelected && (
  <circle
    r="70"
    fill={nodeFill}
stroke={nodeStroke}
    strokeWidth="8"
  />
)}
              {node.type === "WALLET" && (
                <circle
                  r="28"
                  fill={style.fill}
                  stroke={style.stroke}
                  strokeWidth="3"
                />
              )}

              {node.type ===
                "TRANSACTION" && (
                <rect
                  x="-28"
                  y="-28"
                  width="56"
                  height="56"
                  rx="6"
                  fill={nodeFill}
                  stroke={nodeStroke}
                  strokeWidth="3"
                />
              )}

              {node.type === "IP" && (
                <polygon
                  points="0,-32 32,0 0,32 -32,0"
                  fill={nodeFill}
                  stroke={nodeStroke}
                  strokeWidth="3"
                />
              )}

              <text
                textAnchor="middle"
                dominantBaseline="middle"
                fill="#ffffff"
                fontSize="13"
                fontWeight="700"
                fontFamily="monospace"
              >
                {style.label}
              </text>

              <text
                y="48"
                textAnchor="middle"
                fill="#ffffff"
                fontSize="12"
                fontFamily="monospace"
              >
                {node.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}