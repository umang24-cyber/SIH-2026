import React, { useState } from 'react';
import type { GraphNode, GraphEdge } from '../../types/graph';

interface GraphCanvasBackdropProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNodeId: string | null;
  onSelectNode: (node: GraphNode) => void;
}

export const GraphCanvasBackdrop: React.FC<GraphCanvasBackdropProps> = ({
  nodes,
  edges,
  selectedNodeId,
  onSelectNode
}) => {
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  const getNode = (id: string) => nodes.find(n => n.id === id);
  const getNodePosition = (nodeId: string) => {
  const index = nodes.findIndex(node => node.id === nodeId);

  const totalNodes = nodes.length;

  const angle = (index / totalNodes) * Math.PI * 2;

  const radiusX = 35;
  const radiusY = 32;

  return {
    x: 50 + Math.cos(angle) * radiusX,
    y: 50 + Math.sin(angle) * radiusY
  };
};
  return (
    <div className="graph-canvas-container">
      <svg
        width="100%"
        height="100%"
        style={{ position: 'absolute', inset: 0, overflow: 'visible' }}
      >
        <defs>
          {/* Directed arrowhead markers */}
          <marker
            id="arrowhead-sent"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#00ff66" />
          </marker>
          <marker
            id="arrowhead-received"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#00ff66" />
          </marker>
          <marker
            id="arrowhead-broadcast"
            markerWidth="8"
            markerHeight="6"
            refX="7"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 8 3, 0 6" fill="#cc66ff" />
          </marker>
        </defs>

        {/* Directed Transaction Flow Edges (With Animated Fluid Flow) */}
        {edges.map(edge => {
          const sourceNode = getNode(edge.source);
          const targetNode = getNode(edge.target);
          if (!sourceNode || !targetNode) return null;

          const isHighlighted =
            edge.source === selectedNodeId ||
            edge.target === selectedNodeId ||
            edge.source === hoveredNodeId ||
            edge.target === hoveredNodeId;

          const isBroadcast = edge.type === 'BROADCAST';
          const strokeColor = isBroadcast
            ? isHighlighted ? '#ee88ff' : 'rgba(204, 102, 255, 0.5)'
            : isHighlighted ? '#00ff66' : 'rgba(0, 204, 85, 0.45)';

          const strokeWidth = isHighlighted ? 3 : isBroadcast ? 1.5 : 2;

          const sourcePosition = getNodePosition(sourceNode.id);
          const targetPosition = getNodePosition(targetNode.id);

          const x1 = `${sourcePosition.x}%`;
          const y1 = `${sourcePosition.y}%`;
          const x2 = `${targetPosition.x}%`;
          const y2 = `${targetPosition.y}%`;

          return (
            <g key={edge.id}>
              {/* Base Line */}
              <line
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={strokeColor}
                strokeWidth={strokeWidth}
                strokeDasharray={isBroadcast ? '5,5' : 'none'}
                markerEnd={
                  isBroadcast
                    ? 'url(#arrowhead-broadcast)'
                    : 'url(#arrowhead-received)'
                }
              />

              {/* Animated Fluid Flowing Pulse Overlay */}
              <line
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={isBroadcast ? '#ffffff' : '#55ff99'}
                strokeWidth={strokeWidth}
                className="edge-flow-active"
                opacity={isHighlighted ? 0.9 : 0.4}
              />

              {/* High-Readability Amount Badge Along Edge */}
              {edge.amountBtc !== undefined && (
                <text
                  x={`${(sourcePosition.x + targetPosition.x) / 2}%`}
                  y={`${(sourcePosition.y + targetPosition.y) / 2 - 1.5}%`}
                  textAnchor="middle"
                  style={{
                    paintOrder: 'stroke fill',
                    stroke: '#000000',
                    strokeWidth: '4px',
                    strokeLinejoin: 'round',
                    fill: isHighlighted ? '#00ff66' : '#e2e8f0',
                    fontSize: '12px',
                    fontWeight: 700,
                    fontFamily: "'Share Tech Mono', monospace"
                  }}
                >
                  {edge.amountBtc} BTC
                </text>
              )}
            </g>
          );
        })}

        {/* Multi-Entity Heterogeneous Nodes (Wallets, Transactions, IPs) */}
        {nodes.map(node => {
          const isSelected = node.id === selectedNodeId;
          const isHovered = node.id === hoveredNodeId;

          const position = getNodePosition(node.id);

          return (
            <g
              key={node.id}
              onClick={() => onSelectNode(node)}
              onMouseEnter={() => setHoveredNodeId(node.id)}
              onMouseLeave={() => setHoveredNodeId(null)}
              className={isSelected || isHovered ? 'node-glow' : ''}
              style={{ cursor: 'pointer' }}
            >
              {/* Node Geometry based on Type */}
              {node.type === 'WALLET' && (
                /* Hexagonal / Circular Wallet Node */
                <g>
                  <circle
                    cx={`${position.x}%`}
                    cy={`${position.y}%`}
                    r={isSelected ? 20 : 16}
                    fill="#021d0a"
                    stroke={isSelected ? '#00ff66' : '#00cc55'}
                    strokeWidth={isSelected ? 3 : 2}
                  />
                  <text
                    x={`${position.y}%`}
                    y={`${position.y}%`}
                    dy="5"
                    fill="#ffffff"
                    fontSize="13"
                    fontWeight="800"
                    fontFamily="monospace"
                    textAnchor="middle"
                  >
                    W
                  </text>
                </g>
              )}

              {node.type === 'TRANSACTION' && (
                /* Square Transaction Node */
                <g>
                  <rect
                    x={`calc(${position.y}% - ${isSelected ? 18 : 15}px)`}
                    y={`calc(${position.y}% - ${isSelected ? 18 : 15}px)`}
                    width={isSelected ? 36 : 30}
                    height={isSelected ? 36 : 30}
                    fill="#221102"
                    stroke={isSelected ? '#ffbb00' : '#ff7700'}
                    strokeWidth={isSelected ? 3 : 2}
                    rx="3"
                  />
                  <text
                    x={`${position.y}%`}
                    y={`${position.y}%`}
                    dy="5"
                    fill="#ffbb00"
                    fontSize="12"
                    fontWeight="800"
                    fontFamily="monospace"
                    textAnchor="middle"
                  >
                    TX
                  </text>
                </g>
              )}

              {node.type === 'IP' && (
                /* Diamond / Server IP Node */
                <g>
                  <polygon
                    points={`calc(${position.y}%),calc(${position.y}% - 19px) calc(${position.y}% + 19px),calc(${position.y}%) calc(${position.y}%),calc(${position.y}% + 19px) calc(${position.y}% - 19px),calc(${position.y}%)`}
                    fill="#230536"
                    stroke={
                          node.infrastructureType === 'bulletproof_host'
                            ? '#ff3366'
                            : '#bb55ff'
                          }
                    strokeWidth={isSelected ? 3 : 2}
                  />
                  <text
                    x={`${position.y}%`}
                    y={`${position.y}%`}
                    dy="5"
                    fill="#ffffff"
                    fontSize="11"
                    fontWeight="800"
                    fontFamily="monospace"
                    textAnchor="middle"
                  >
                    IP
                  </text>
                </g>
              )}

              {/* High Readability Node Label with Black Stroke Halo */}
              <text
                x={`${position.y}%`}
                y={`${position.y}%`}
                dy="32"
                textAnchor="middle"
                style={{
                  paintOrder: 'stroke fill',
                  stroke: '#000000',
                  strokeWidth: '4.5px',
                  strokeLinejoin: 'round',
                  fill: isSelected ? '#00ff66' : '#ffffff',
                  fontSize: '13px',
                  fontWeight: isSelected ? 800 : 700,
                  fontFamily: "'Share Tech Mono', 'Consolas', monospace",
                  letterSpacing: '0.4px'
                }}
              >
                {node.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
