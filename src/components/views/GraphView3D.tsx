/**
 * GraphView3D.tsx  ──  Point-Cloud + Detail-on-Demand renderer
 * ─────────────────────────────────────────────────────────────
 * Architecture:
 *   BULK LAYER  →  single THREE.Points (460k nodes) + single THREE.LineSegments
 *                  Both built from Float32Array buffers delivered by Web Worker
 *   DETAIL LAYER → THREE.Mesh cubes + Canvas Sprites ONLY for:
 *                    • Nodes of the currently active candidate (hovered or selected)
 *                    • The one node under the cursor (raycasted via Points threshold)
 *   RAYCASTING   → raycaster.params.Points.threshold set to world-space radius
 *                  Nearest-hit index → look up nodeIds[] → show hover card
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { ForensicNode } from '../../types/terminal';
import type { GraphPayload } from '../../workers/graphLoader.worker';

// ─── Props ────────────────────────────────────────────────────────────────────
interface GraphView3DProps {
  /** Curated node metadata used for inspect commands and hover details. */
  nodes: ForensicNode[];
  /** Retained for compatibility with the terminal data model. */
  links: unknown[];
  /** Scenario fetched from the live backend graph endpoint. */
  scenarioId: string;
  highlightedNodeId?: string | null;
  onSelectNode: (nodeId: string) => void;
  onRunCommand: (cmd: string) => void;
}

// ─── Load state ───────────────────────────────────────────────────────────────
type LoadState =
  | { status: 'idle' }
  | { status: 'loading'; pct: number; message: string }
  | { status: 'done'; payload: GraphPayload }
  | { status: 'error'; message: string };

// ─── Cluster filter mode ──────────────────────────────────────────────────────
type FilterMode = 'ALL' | 'PEEL' | 'LAYER' | 'MIX';

// ─── Colour constants (mirrored from worker) ──────────────────────────────────
const COL_BENIGN       = new THREE.Color(0x005a1e);
const COL_PEELING      = new THREE.Color(0xdc2814);
const COL_LAYERING     = new THREE.Color(0xf08c00);
const COL_MIXING       = new THREE.Color(0x3c78ff);
const COL_TRANSACTION  = new THREE.Color(0x1e5082);
const COL_IP           = new THREE.Color(0xa07800);
const COL_HOVER        = new THREE.Color(0x00ff88);

// ─── Detail-layer geometry (shared, allocated once) ──────────────────────────
const DETAIL_BOX_GEO = new THREE.BoxGeometry(6, 6, 6);
const DETAIL_WIRE_GEO = new THREE.WireframeGeometry(DETAIL_BOX_GEO);

function makeDetailGroup(
  pos: THREE.Vector3,
  label: string,
  isHighRisk: boolean
): THREE.Group {
  const group = new THREE.Group();
  group.position.copy(pos);

  const wireColor = isHighRisk ? 0xff3344 : 0x00cc55;
  const wireMat = new THREE.LineBasicMaterial({ color: wireColor });
  group.add(new THREE.LineSegments(DETAIL_WIRE_GEO, wireMat));

  const coreMat = new THREE.MeshBasicMaterial({
    color: isHighRisk ? 0x440011 : 0x003311,
    transparent: true,
    opacity: 0.8,
  });
  const mesh = new THREE.Mesh(DETAIL_BOX_GEO, coreMat);
  group.add(mesh);

  // Canvas sprite label
  const canvas = document.createElement('canvas');
  canvas.width = 256; canvas.height = 56;
  const ctx = canvas.getContext('2d')!;
  ctx.fillStyle = '#000000';
  ctx.fillRect(0, 0, 256, 56);
  ctx.strokeStyle = isHighRisk ? '#ff3344' : '#00cc55';
  ctx.lineWidth = 2;
  ctx.strokeRect(2, 2, 252, 52);
  ctx.font = 'bold 18px monospace';
  ctx.fillStyle = isHighRisk ? '#ff5566' : '#33ff88';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(`[${label.slice(0, 12)}…]`, 128, 20);
  ctx.font = '13px monospace';
  ctx.fillStyle = '#a0e2bf';
  ctx.fillText(isHighRisk ? 'HIGH RISK' : 'CANDIDATE NODE', 128, 40);

  const tex = new THREE.CanvasTexture(canvas);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
  sprite.scale.set(20, 4.4, 1);
  sprite.position.set(0, 9, 0);
  group.add(sprite);

  return group;
}

// ─── Component ────────────────────────────────────────────────────────────────
export const GraphView3D: React.FC<GraphView3DProps> = ({
  nodes: showcaseNodes,
  links: _showcaseLinks,
  scenarioId,
  highlightedNodeId,
  onSelectNode,
  onRunCommand,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // ── Worker load state
  const [loadState, setLoadState] = useState<LoadState>({ status: 'idle' });

  // ── Hover / selection state (React-managed so hover card re-renders cleanly)
  const [hoveredId, setHoveredId]     = useState<string | null>(null);
  const [selectedId, setSelectedId]   = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<FilterMode>('ALL');

  // ── Refs so the effect closure can read mutable state without re-running
  const payloadRef      = useRef<GraphPayload | null>(null);
  const activeFilterRef = useRef<FilterMode>('ALL');
  const rendererRef     = useRef<THREE.WebGLRenderer | null>(null);

  // Keep filter ref in sync
  useEffect(() => { activeFilterRef.current = activeFilter; }, [activeFilter]);

  // ─── 1. Kick off the Web Worker once on mount ────────────────────────────
  useEffect(() => {
    setLoadState({ status: 'loading', pct: 1, message: 'Initialising graph loader …' });

    const worker = new Worker(
      new URL('../../workers/graphLoader.worker.ts', import.meta.url),
      { type: 'module' }
    );

    worker.onmessage = (e: MessageEvent) => {
      const msg = e.data;
      if (msg.type === 'PROGRESS') {
        setLoadState({ status: 'loading', pct: msg.pct, message: msg.message });
      } else if (msg.type === 'DONE') {
        payloadRef.current = msg.payload as GraphPayload;
        setLoadState({ status: 'done', payload: msg.payload as GraphPayload });
      } else if (msg.type === 'ERROR') {
        setLoadState({ status: 'error', message: msg.message });
      }
    };
    worker.onerror = (e) => {
      setLoadState({ status: 'error', message: e.message });
    };

    // Kick off
    worker.postMessage({ type: 'start', scenarioId });

    return () => worker.terminate();
  }, [scenarioId]);

  // ─── 2. Build / rebuild Three.js scene once data arrives ─────────────────
  useEffect(() => {
    if (loadState.status !== 'done') return;
    const container = containerRef.current;
    if (!container) return;

    const payload = loadState.payload;

    // ── Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);
    scene.fog = new THREE.FogExp2(0x000000, 0.0005);

    const width  = container.clientWidth  || 900;
    const height = container.clientHeight || 500;
    const camera = new THREE.PerspectiveCamera(55, width / height, 0.5, 2000);
    camera.position.set(0, 0, 450);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setLoadState({ status: 'error', message: `WebGL renderer unavailable: ${message}` });
      return;
    }
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.domElement.style.display = 'block';
    renderer.domElement.style.width = '100%';
    renderer.domElement.style.height = '100%';
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // ── BULK: All nodes as a single THREE.Points (1 draw call)
    const pointsGeo = new THREE.BufferGeometry();
    pointsGeo.setAttribute('position', new THREE.BufferAttribute(payload.positions, 3));
    pointsGeo.setAttribute('color',    new THREE.BufferAttribute(
      // Normalise Uint8 → Float32 for THREE
      Float32Array.from(payload.colors, v => v / 255), 3
    ));
    pointsGeo.computeBoundingSphere();

    const pointsMat = new THREE.PointsMaterial({
      size: 1.6,
      vertexColors: true,
      transparent: true,
      opacity: 0.75,
      sizeAttenuation: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const pointCloud = new THREE.Points(pointsGeo, pointsMat);
    scene.add(pointCloud);

    // ── BULK: Sampled edges as a single THREE.LineSegments (1 draw call)
    const edgesGeo = new THREE.BufferGeometry();
    edgesGeo.setAttribute('position', new THREE.BufferAttribute(payload.edgePositions, 3));
    const edgesMat = new THREE.LineBasicMaterial({
      color: 0x004d18,
      transparent: true,
      opacity: 0.28,
    });
    const edgeLines = new THREE.LineSegments(edgesGeo, edgesMat);
    scene.add(edgeLines);

    // ── Background galaxy point cloud (ambient context, 2000 pts)
    {
      const bgCount = 2000;
      const bgPos   = new Float32Array(bgCount * 3);
      const bgCol   = new Float32Array(bgCount * 3);
      for (let i = 0; i < bgCount; i++) {
        const u = Math.random(), v = Math.random();
        const theta = u * 2 * Math.PI;
        const phi   = Math.acos(2 * v - 1);
        const r     = Math.cbrt(Math.random()) * 350 + 80;
        bgPos[i*3]   = r * Math.sin(phi) * Math.cos(theta);
        bgPos[i*3+1] = r * Math.sin(phi) * Math.sin(theta) * 0.4;
        bgPos[i*3+2] = r * Math.cos(phi);
        bgCol[i*3]   = 0.02 + Math.random() * 0.05;
        bgCol[i*3+1] = 0.12 + Math.random() * 0.22;
        bgCol[i*3+2] = 0.04 + Math.random() * 0.06;
      }
      const bgGeo = new THREE.BufferGeometry();
      bgGeo.setAttribute('position', new THREE.BufferAttribute(bgPos, 3));
      bgGeo.setAttribute('color',    new THREE.BufferAttribute(bgCol, 3));
      scene.add(new THREE.Points(bgGeo, new THREE.PointsMaterial({
        size: 1.8, vertexColors: true, transparent: true, opacity: 0.4,
        blending: THREE.AdditiveBlending, depthWrite: false,
      })));
    }

    // ── DETAIL LAYER: mutable group, rebuilt when selection changes
    let detailGroup = new THREE.Group();
    scene.add(detailGroup);

    // Hover highlight: single pulsing point-size sprite mesh
    const hoverGeo  = new THREE.SphereGeometry(4, 8, 8);
    const hoverMat  = new THREE.MeshBasicMaterial({ color: 0x00ff88, transparent: true, opacity: 0.9 });
    const hoverMesh = new THREE.Mesh(hoverGeo, hoverMat);
    hoverMesh.visible = false;
    scene.add(hoverMesh);

    // ── Raycaster (against the Points bulk layer)
    const raycaster = new THREE.Raycaster();
    raycaster.params.Points = { threshold: 3.5 }; // world-space units
    const mouse = new THREE.Vector2();

    // ── Mouse controls
    let isDragging = false, isRightDragging = false;
    let prevMouse  = { x: 0, y: 0 };
    const ROTATE_SPEED = 0.003;
    let currentHoveredIdx: number | null = null;

    const onMouseDown = (e: MouseEvent) => {
      if (e.button === 0) isDragging = true;
      if (e.button === 2) isRightDragging = true;
      prevMouse = { x: e.clientX, y: e.clientY };
    };
    const onMouseUp = () => { isDragging = false; isRightDragging = false; };
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      camera.position.z = Math.max(80, Math.min(900, camera.position.z + e.deltaY * 0.22));
    };

    const onMouseMove = (e: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x =  ((e.clientX - rect.left) / rect.width)  * 2 - 1;
      mouse.y = -((e.clientY - rect.top)  / rect.height)  * 2 + 1;

      if (isDragging) {
        scene.rotation.y += (e.clientX - prevMouse.x) * ROTATE_SPEED;
        scene.rotation.x += (e.clientY - prevMouse.y) * ROTATE_SPEED;
      } else if (isRightDragging) {
        camera.position.x -= (e.clientX - prevMouse.x) * 0.25;
        camera.position.y += (e.clientY - prevMouse.y) * 0.25;
      }
      prevMouse = { x: e.clientX, y: e.clientY };

      // Raycast against bulk Points
      raycaster.setFromCamera(mouse, camera);
      const hits = raycaster.intersectObject(pointCloud);

      if (hits.length > 0) {
        const idx = hits[0].index!;
        if (idx !== currentHoveredIdx) {
          currentHoveredIdx = idx;
          setHoveredId(payload.nodeIds[idx]);

          // Move hover mesh to hit position
          hoverMesh.position.set(
            payload.positions[idx * 3],
            payload.positions[idx * 3 + 1],
            payload.positions[idx * 3 + 2]
          );
          hoverMesh.visible = true;
        }
      } else {
        currentHoveredIdx = null;
        setHoveredId(null);
        hoverMesh.visible = false;
      }
    };

    const onClick = () => {
      if (currentHoveredIdx === null) return;
      const nodeId = payload.nodeIds[currentHoveredIdx];
      setSelectedId(nodeId);

      // Build detail meshes for this node and its candidate
      scene.remove(detailGroup);
      detailGroup.traverse(o => {
        if ((o as THREE.Mesh).geometry) (o as THREE.Mesh).geometry.dispose();
        if ((o as THREE.Mesh).material) {
          const m = (o as THREE.Mesh).material;
          if (Array.isArray(m)) m.forEach(x => x.dispose());
          else (m as THREE.Material).dispose();
        }
      });
      detailGroup = new THREE.Group();
      scene.add(detailGroup);

      // Spawn detail for the clicked node
      const pos = new THREE.Vector3(
        payload.positions[currentHoveredIdx * 3],
        payload.positions[currentHoveredIdx * 3 + 1],
        payload.positions[currentHoveredIdx * 3 + 2]
      );
      detailGroup.add(makeDetailGroup(pos, nodeId, false));

      // Notify parent (triggers inspect command)
      // Strip prefix: "w:", "tx:", "ip:"
      const cleanId = nodeId.replace(/^(w:|tx:|ip:)/, '');
      onSelectNode(cleanId);
    };

    const domEl = renderer.domElement;
    domEl.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    domEl.addEventListener('click', onClick);
    domEl.addEventListener('wheel', onWheel, { passive: false });
    domEl.addEventListener('contextmenu', e => e.preventDefault());

    // ── Animation loop
    let rafId: number;
    const animate = () => {
      rafId = requestAnimationFrame(animate);

      // Slow auto-rotate
      if (!isDragging && !isRightDragging) {
        scene.rotation.y += 0.0005;
      }

      // Pulse hover mesh
      if (hoverMesh.visible) {
        const s = 1 + Math.sin(Date.now() * 0.006) * 0.18;
        hoverMesh.scale.setScalar(s);
      }

      renderer.render(scene, camera);
    };
    animate();

    // ── Resize
    const onResize = () => {
      if (!container) return;
      const w = container.clientWidth, h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(rafId);
      domEl.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      domEl.removeEventListener('click', onClick);
      domEl.removeEventListener('wheel', onWheel);
      window.removeEventListener('resize', onResize);
      if (container.contains(domEl)) container.removeChild(domEl);
      renderer.dispose();
      rendererRef.current = null;
      pointsGeo.dispose();
      edgesGeo.dispose();
    };
    // Only re-run when the payload arrives (once). The eslint disable is intentional:
    // we want to run exactly once per payload object, not on every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadState.status]);

  // ── Find hovered node data for the hover card ────────────────────────────
  const hoveredNode = hoveredId
    ? showcaseNodes.find(n => n.id === hoveredId.replace(/^(w:|tx:|ip:)/, ''))
    : null;

  const payload = loadState.status === 'done' ? loadState.payload : null;

  // Find active candidate (for filter buttons label)
  const candidateCount = payload?.candidateCount ?? 0;

  const handleFilterClick = useCallback((f: FilterMode) => {
    setActiveFilter(f);
  }, []);

  return (
    <div style={{ position: 'relative', width: '100%', height: '520px', minHeight: '520px' }}>

      {/* ── WebGL Canvas */}
      <div
        ref={containerRef}
        style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0, zIndex: 0 }}
      />

      {/* ── Loading Overlay */}
      {loadState.status === 'loading' && (
        <div style={{
          position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
          background: 'rgba(0,0,0,0.88)', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', zIndex: 20,
          fontFamily: 'monospace',
        }}>
          <div style={{ color: '#00ff66', fontSize: '14px', marginBottom: '14px', fontWeight: 600 }}>
            LIVE GRAPH ENGINE INITIALISING …
          </div>
          <div style={{
            width: '340px', height: '8px', background: '#111',
            border: '1px solid #007a33', borderRadius: '2px', overflow: 'hidden',
          }}>
            <div style={{
              width: `${loadState.pct}%`, height: '100%',
              background: 'linear-gradient(90deg, #007a33, #00ff66)',
              transition: 'width 0.4s ease',
            }} />
          </div>
          <div style={{ color: '#557766', fontSize: '12px', marginTop: '8px' }}>
            {loadState.message}
          </div>
          <div style={{ color: '#333', fontSize: '11px', marginTop: '16px' }}>
            Fetching scenario graph from the FastAPI backend …
          </div>
        </div>
      )}

      {/* ── Error Overlay */}
      {loadState.status === 'error' && (
        <div style={{
          position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
          background: 'rgba(0,0,0,0.92)', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', zIndex: 20, fontFamily: 'monospace',
        }}>
          <div style={{ color: '#ff3344', fontSize: '14px', marginBottom: '8px' }}>
            ✗ GRAPH LOAD FAILED
          </div>
          <div style={{ color: '#888', fontSize: '12px', maxWidth: '400px', textAlign: 'center' }}>
            {loadState.message}
          </div>
          <div style={{ color: '#444', fontSize: '11px', marginTop: '12px' }}>
            Ensure the backend is running and scenario <code>{scenarioId}</code> exists.
          </div>
        </div>
      )}

      {/* ── HUD Overlay (top-left) */}
      {loadState.status === 'done' && (
        <div style={{
          position: 'absolute', top: 10, left: 12,
          background: 'rgba(0,16,6,0.88)', border: '1px solid #007a33',
          padding: '10px 14px', fontSize: '13px', zIndex: 5, fontFamily: 'monospace',
        }}>
          <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '3px' }}>
            3D BITCOIN AML TOPOLOGY :: LIVE V7 SCENARIO
          </div>
          <div style={{ color: '#00ff66', fontSize: '12px' }}>
            NODES: {payload!.nodeCount.toLocaleString()} &nbsp;|&nbsp;
            EDGES: {payload!.edgeCount.toLocaleString()} &nbsp;|&nbsp;
            CANDIDATES: {candidateCount.toLocaleString()}
          </div>
          <div style={{ color: '#007a33', marginTop: '3px', fontSize: '11px' }}>
            [Left-Drag] Rotate &nbsp;|&nbsp; [Right-Drag] Pan &nbsp;|&nbsp;
            [Scroll] Zoom &nbsp;|&nbsp; [Click] Inspect Node
          </div>

          {/* Legend */}
          <div style={{ marginTop: '6px', display: 'flex', gap: '10px', flexWrap: 'wrap', fontSize: '11px' }}>
            {[
              { col: '#dc2814', label: 'Peeling Chain' },
              { col: '#f08c00', label: 'Layering' },
              { col: '#3c78ff', label: 'Mixing / CoinJoin' },
              { col: '#005a1e', label: 'Benign Wallet' },
            ].map(({ col, label }) => (
              <span key={label} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: col, display: 'inline-block' }} />
                <span style={{ color: '#778' }}>{label}</span>
              </span>
            ))}
          </div>

          {/* Typology filter buttons */}
          <div style={{ marginTop: '8px', display: 'flex', gap: '6px', alignItems: 'center' }}>
            <span style={{ color: '#558866', fontSize: '11px' }}>SCOPE:</span>
            {(['ALL', 'PEEL', 'LAYER', 'MIX'] as FilterMode[]).map(mode => (
              <button
                key={mode}
                onClick={() => handleFilterClick(mode)}
                style={{
                  background: activeFilter === mode ? '#00cc55' : '#030d05',
                  color:      activeFilter === mode ? '#000' : '#33ff88',
                  border:     '1px solid #007a33',
                  padding:    '2px 7px',
                  fontSize:   '11px',
                  fontWeight: 'bold',
                  cursor:     'pointer',
                  fontFamily: 'monospace',
                }}
              >
                [{mode}]
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Hover / Selected Node Card (bottom-right) */}
      {hoveredId && (
        <div style={{
          position: 'absolute', bottom: 12, right: 12,
          width: '340px',
          background: 'rgba(0,14,5,0.96)', border: '1px solid #00ff66',
          padding: '12px', zIndex: 10, fontSize: '13px', fontFamily: 'monospace',
        }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between',
            borderBottom: '1px dashed #007a33', paddingBottom: '4px', marginBottom: '6px',
          }}>
            <strong style={{ color: '#33ff88' }}>[{hoveredId.slice(0, 18)}…]</strong>
            <span style={{ color: '#558', fontSize: '11px' }}>HOVER · CLICK TO INSPECT</span>
          </div>
          <p style={{ color: '#a0e2bf', wordBreak: 'break-all', margin: '3px 0' }}>
            <strong>RAW ID:</strong> {hoveredId}
          </p>
          {hoveredNode ? (
            <>
              <p style={{ margin: '3px 0' }}><strong>LABEL:</strong> {hoveredNode.label}</p>
              <p style={{ margin: '3px 0' }}><strong>TYPE:</strong> {hoveredNode.type}</p>
              <p style={{ margin: '3px 0' }}>
                <strong>RISK:</strong>{' '}
                <span style={{ color: hoveredNode.riskScore >= 80 ? '#ff3344' : '#22c55e', fontWeight: 'bold' }}>
                  {hoveredNode.riskScore}/100
                </span>
              </p>
              <p style={{ margin: '3px 0' }}><strong>CLUSTER:</strong> {hoveredNode.clusterId}</p>
              <div style={{
                marginTop: '8px', borderTop: '1px dashed #007a33', paddingTop: '6px',
                display: 'flex', gap: '8px',
              }}>
                <span
                  className="cmd-tag"
                  style={{ fontSize: '11px', cursor: 'pointer' }}
                  onClick={() => onRunCommand(`inspect ${hoveredNode.id}`)}
                >
                  {'>'} inspect {hoveredNode.id.slice(0, 10)}…
                </span>
              </div>
            </>
          ) : (
            <p style={{ color: '#556', margin: '3px 0', fontSize: '12px' }}>
              {hoveredId.startsWith('tx:') ? 'TRANSACTION NODE' :
               hoveredId.startsWith('ip:') ? 'IP/RELAY NODE' : 'WALLET NODE'}
              &nbsp;— Click to run inspect
            </p>
          )}
        </div>
      )}

      {/* ── Selected node banner */}
      {selectedId && !hoveredId && (
        <div style={{
          position: 'absolute', bottom: 12, right: 12,
          width: '340px',
          background: 'rgba(0,14,5,0.92)', border: '1px solid #007a33',
          padding: '10px 12px', zIndex: 10, fontSize: '12px', fontFamily: 'monospace',
        }}>
          <div style={{ color: '#33ff88' }}>SELECTED: {selectedId.slice(0, 22)}…</div>
          <div style={{ color: '#445', marginTop: '3px' }}>
            Inspect command triggered. Hover another node to continue.
          </div>
        </div>
      )}
    </div>
  );
};
