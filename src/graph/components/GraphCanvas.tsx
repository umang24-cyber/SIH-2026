import React, { useEffect, useRef, useState, useMemo } from 'react';
import * as THREE from 'three';
import type { GraphData, GraphNode, GraphEdge, GraphMode } from '../../types/graph';

interface GraphCanvasProps {
  data: GraphData;
  mode: GraphMode;
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string | null) => void;
}

// Pre-generate crisp Bitcoin medallion canvas textures
function createBitcoinTexture(colorHex: string, symbol: string = '₿'): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext('2d');
  if (!ctx) return new THREE.CanvasTexture(canvas);

  const cx = 64;
  const cy = 64;

  // Outer halation glow
  const glowGrad = ctx.createRadialGradient(cx, cy, 38, cx, cy, 62);
  glowGrad.addColorStop(0, colorHex + '66');
  glowGrad.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = glowGrad;
  ctx.beginPath();
  ctx.arc(cx, cy, 62, 0, Math.PI * 2);
  ctx.fill();

  // Outer metallic coin rim
  ctx.beginPath();
  ctx.arc(cx, cy, 46, 0, Math.PI * 2);
  ctx.fillStyle = '#111812';
  ctx.fill();
  ctx.lineWidth = 4;
  ctx.strokeStyle = colorHex;
  ctx.stroke();

  // Inner coin bezel
  ctx.beginPath();
  ctx.arc(cx, cy, 40, 0, Math.PI * 2);
  ctx.lineWidth = 1.5;
  ctx.strokeStyle = colorHex + 'aa';
  ctx.stroke();

  // Circuit notches around perimeter
  for (let i = 0; i < 12; i++) {
    const angle = (i * Math.PI * 2) / 12;
    const nx = cx + Math.cos(angle) * 43;
    const ny = cy + Math.sin(angle) * 43;
    ctx.beginPath();
    ctx.arc(nx, ny, 1.8, 0, Math.PI * 2);
    ctx.fillStyle = colorHex;
    ctx.fill();
  }

  // Coin face disk
  const diskGrad = ctx.createRadialGradient(cx - 8, cy - 8, 4, cx, cy, 38);
  diskGrad.addColorStop(0, '#1f2e22');
  diskGrad.addColorStop(0.7, '#0b140d');
  diskGrad.addColorStop(1, '#050a06');
  ctx.beginPath();
  ctx.arc(cx, cy, 38, 0, Math.PI * 2);
  ctx.fillStyle = diskGrad;
  ctx.fill();

  // Center symbol (Tilted ₿ or icon)
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(symbol === '₿' ? 0.18 : 0);
  ctx.font = symbol === '₿' ? 'bold 44px "Courier New", monospace' : 'bold 36px "Courier New", monospace';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillStyle = colorHex;
  ctx.shadowColor = colorHex;
  ctx.shadowBlur = 8;
  ctx.fillText(symbol, 0, 0);
  ctx.restore();

  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  return texture;
}

// Text label texture
function createTextLabelTexture(text: string, colorHex: string): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 64;
  const ctx = canvas.getContext('2d');
  if (!ctx) return new THREE.CanvasTexture(canvas);

  ctx.fillStyle = '#050a06cc';
  ctx.roundRect ? ctx.roundRect(4, 12, 248, 40, 6) : ctx.fillRect(4, 12, 248, 40);
  ctx.fill();

  ctx.strokeStyle = colorHex + 'aa';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  ctx.font = 'bold 20px "Courier New", monospace';
  ctx.fillStyle = '#e0ffe8';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 128, 32);

  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  return texture;
}

export const GraphCanvas: React.FC<GraphCanvasProps> = ({
  data,
  selectedNodeId,
  onSelectNode,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [showOrbs, setShowOrbs] = useState<boolean>(true);
  const [autoRotate, setAutoRotate] = useState<boolean>(true);

  // Textures cache for high performance
  const textures = useMemo(() => {
    return {
      green: createBitcoinTexture('#00ff66', '₿'),
      orange: createBitcoinTexture('#ffaa00', '₿'),
      red: createBitcoinTexture('#ff3344', '₿'),
      tx: createBitcoinTexture('#ffd700', 'TX'),
      ip: createBitcoinTexture('#00ccff', 'IP'),
    };
  }, []);

  const controlsRef = useRef<{
    zoomIn: () => void;
    zoomOut: () => void;
    resetView: () => void;
    fitView: () => void;
  } | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let width = container.clientWidth || 900;
    let height = container.clientHeight || 550;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x020603);
    scene.fog = new THREE.FogExp2(0x020603, 0.0018);

    const camera = new THREE.PerspectiveCamera(50, width / height, 1, 3000);
    camera.position.set(0, 0, 320);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.domElement.style.display = 'block';
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 2. Compute 3D Force-Directed Positions
    const nodes = data.nodes || [];
    const edges = data.edges || [];
    const nodeCount = nodes.length;

    const nodePositions = new Map<string, THREE.Vector3>();

    if (nodeCount > 0) {
      // Fibonacci sphere initialization with repulsive relaxation
      nodes.forEach((node, i) => {
        const phi = Math.acos(-1 + (2 * (i + 0.5)) / nodeCount);
        const theta = Math.sqrt(nodeCount * Math.PI) * phi;
        const radius = 100 + (node.riskScore ? node.riskScore * 30 : 15);
        const x = radius * Math.cos(theta) * Math.sin(phi);
        const y = radius * Math.sin(theta) * Math.sin(phi);
        const z = radius * Math.cos(phi) * 0.7; // slight flattening for better camera depth
        nodePositions.set(node.id, new THREE.Vector3(x, y, z));
      });

      // Simple fast 3D relaxation steps based on edges
      const edgeWeight = 0.06;
      for (let step = 0; step < 25; step++) {
        edges.forEach(edge => {
          const p1 = nodePositions.get(edge.source);
          const p2 = nodePositions.get(edge.target);
          if (p1 && p2) {
            const delta = new THREE.Vector3().subVectors(p2, p1);
            const dist = delta.length();
            const desiredDist = 70;
            if (dist > 0.1) {
              const force = (dist - desiredDist) * edgeWeight;
              delta.normalize().multiplyScalar(force * 0.5);
              p1.add(delta);
              p2.sub(delta);
            }
          }
        });
      }
    }

    // 3. Build Node Sprites
    const spriteGroup = new THREE.Group();
    const hitMeshGroup = new THREE.Group();
    const nodeObjMap = new Map<string, { sprite: THREE.Sprite; pos: THREE.Vector3; node: GraphNode }>();

    nodes.forEach(node => {
      const pos = nodePositions.get(node.id) || new THREE.Vector3();
      const risk = node.riskScore ?? 0.2;

      // Select texture based on node type and trust level
      let tex = textures.green;
      let colorHex = '#00ff66';
      if (node.type === 'TRANSACTION') {
        tex = textures.tx;
        colorHex = '#ffd700';
      } else if (node.type === 'IP') {
        tex = textures.ip;
        colorHex = '#00ccff';
      } else if (risk > 0.75) {
        tex = textures.red;
        colorHex = '#ff3344';
      } else if (risk >= 0.40) {
        tex = textures.orange;
        colorHex = '#ffaa00';
      }

      // Medallion Sprite
      const spriteMat = new THREE.SpriteMaterial({
        map: tex,
        transparent: true,
        depthWrite: false,
      });
      const sprite = new THREE.Sprite(spriteMat);
      const isSelected = node.id === selectedNodeId;
      const scale = isSelected ? 26 : 20;
      sprite.scale.set(scale, scale, 1);
      sprite.position.copy(pos);
      spriteGroup.add(sprite);

      // Label Sprite
      const shortLabel = node.label ? (node.label.length > 14 ? node.label.slice(0, 12) + '..' : node.label) : node.id.slice(0, 8);
      const labelTex = createTextLabelTexture(`[${shortLabel}]`, colorHex);
      const labelMat = new THREE.SpriteMaterial({ map: labelTex, transparent: true, depthWrite: false });
      const labelSprite = new THREE.Sprite(labelMat);
      labelSprite.scale.set(22, 5.5, 1);
      labelSprite.position.set(pos.x, pos.y - 12, pos.z);
      spriteGroup.add(labelSprite);

      // Invisible sphere mesh for accurate raycast click/hover hit detection
      const hitGeo = new THREE.SphereGeometry(12, 8, 8);
      const hitMat = new THREE.MeshBasicMaterial({ visible: false });
      const hitMesh = new THREE.Mesh(hitGeo, hitMat);
      hitMesh.position.copy(pos);
      hitMesh.userData = { nodeId: node.id };
      hitMeshGroup.add(hitMesh);

      nodeObjMap.set(node.id, { sprite, pos, node });
    });

    scene.add(spriteGroup);
    scene.add(hitMeshGroup);

    // 4. Build Directed 3D Edges & Animated Moving Orbs
    const edgeLinesGroup = new THREE.Group();
    const orbsGroup = new THREE.Group();

    interface OrbData {
      mesh: THREE.Mesh;
      src: THREE.Vector3;
      dst: THREE.Vector3;
      progress: number;
      speed: number;
    }

    const orbs: OrbData[] = [];
    const orbGeo = new THREE.SphereGeometry(1.8, 8, 8);

    edges.forEach(edge => {
      const srcPos = nodePositions.get(edge.source);
      const dstPos = nodePositions.get(edge.target);
      if (srcPos && dstPos) {
        // Directed 3D line
        const points = [srcPos, dstPos];
        const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
        const lineMat = new THREE.LineBasicMaterial({
          color: edge.type === 'BROADCAST' ? 0x00aaff : 0x007a33,
          transparent: true,
          opacity: 0.55,
        });
        const line = new THREE.Line(lineGeo, lineMat);
        edgeLinesGroup.add(line);

        // Animated Transaction Orb
        const orbColor = edge.amountBtc && edge.amountBtc > 10 ? 0xffaa00 : 0x33ff88;
        const orbMat = new THREE.MeshBasicMaterial({ color: orbColor });
        const orbMesh = new THREE.Mesh(orbGeo, orbMat);
        orbMesh.position.copy(srcPos);
        orbsGroup.add(orbMesh);

        // Calculate speed proportional to BTC amount (capped between 0.004 and 0.015)
        const amt = edge.amountBtc || 1.0;
        const speed = Math.min(0.016, 0.005 + (amt / 50) * 0.005);

        orbs.push({
          mesh: orbMesh,
          src: srcPos,
          dst: dstPos,
          progress: Math.random(), // desynchronize orbs across links
          speed,
        });
      }
    });

    scene.add(edgeLinesGroup);
    scene.add(orbsGroup);

    // 5. Mouse & Touch Orbit Controls (Native WebGL event listener)
    let isDragging = false;
    let isRightDragging = false;
    let prevMouse = { x: 0, y: 0 };
    const rotationSpeed = 0.005;

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const onMouseDown = (e: MouseEvent) => {
      if (e.button === 0) isDragging = true;
      if (e.button === 2) isRightDragging = true;
      prevMouse = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      if (isDragging) {
        const deltaX = e.clientX - prevMouse.x;
        const deltaY = e.clientY - prevMouse.y;
        scene.rotation.y += deltaX * rotationSpeed;
        scene.rotation.x += deltaY * rotationSpeed;
      } else if (isRightDragging) {
        const deltaX = e.clientX - prevMouse.x;
        const deltaY = e.clientY - prevMouse.y;
        camera.position.x -= deltaX * 0.25;
        camera.position.y += deltaY * 0.25;
      }

      prevMouse = { x: e.clientX, y: e.clientY };

      // Raycast for hover detection
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(hitMeshGroup.children);
      if (intersects.length > 0) {
        const hitId = intersects[0].object.userData.nodeId;
        const found = nodes.find(n => n.id === hitId) || null;
        setHoveredNode(found);
      } else {
        setHoveredNode(null);
      }
    };

    const onMouseUp = () => {
      isDragging = false;
      isRightDragging = false;
    };

    const onClick = (e: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(hitMeshGroup.children);
      if (intersects.length > 0) {
        const hitId = intersects[0].object.userData.nodeId;
        onSelectNode(hitId);
      }
    };

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      camera.position.z += e.deltaY * 0.2;
      camera.position.z = Math.max(60, Math.min(650, camera.position.z));
    };

    const dom = renderer.domElement;
    dom.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    dom.addEventListener('click', onClick);
    dom.addEventListener('wheel', onWheel, { passive: false });
    dom.addEventListener('contextmenu', e => e.preventDefault());

    // 6. Window Resize
    const handleResize = () => {
      if (!container) return;
      width = container.clientWidth;
      height = container.clientHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    window.addEventListener('resize', handleResize);

    // 7. Animation Loop (Silky Smooth 60 FPS)
    let reqId: number;
    const animate = () => {
      reqId = requestAnimationFrame(animate);

      // Auto-rotation if enabled and user not dragging
      if (autoRotate && !isDragging && !isRightDragging) {
        scene.rotation.y += 0.0015;
      }

      // Animate directional transaction orbs
      if (showOrbs) {
        orbsGroup.visible = true;
        for (let i = 0; i < orbs.length; i++) {
          const orb = orbs[i];
          orb.progress += orb.speed;
          if (orb.progress > 1) orb.progress = 0;
          orb.mesh.position.lerpVectors(orb.src, orb.dst, orb.progress);
        }
      } else {
        orbsGroup.visible = false;
      }

      renderer.render(scene, camera);
    };

    animate();

    // Wire HUD controls
    controlsRef.current = {
      zoomIn: () => {
        camera.position.z = Math.max(60, camera.position.z - 40);
      },
      zoomOut: () => {
        camera.position.z = Math.min(650, camera.position.z + 40);
      },
      resetView: () => {
        scene.rotation.set(0, 0, 0);
        camera.position.set(0, 0, 320);
      },
      fitView: () => {
        scene.rotation.set(0, 0, 0);
        camera.position.set(0, 0, 240);
      }
    };

    // Cleanup
    return () => {
      cancelAnimationFrame(reqId);
      dom.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      dom.removeEventListener('click', onClick);
      dom.removeEventListener('wheel', onWheel);
      dom.removeEventListener('contextmenu', e => e.preventDefault());
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, [data, selectedNodeId, textures, showOrbs, autoRotate]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '520px', background: '#020603', overflow: 'hidden', border: '1px solid #004d20' }}>
      {/* Three.js Canvas mount container */}
      <div ref={containerRef} style={{ width: '100%', height: '100%', cursor: 'grab' }} />

      {/* 3D HUD Controls Toolbar */}
      <div
        style={{
          position: 'absolute',
          top: '10px',
          right: '10px',
          display: 'flex',
          gap: '6px',
          background: 'rgba(0, 14, 6, 0.85)',
          padding: '4px 8px',
          borderRadius: '3px',
          border: '1px solid #00ff66',
          zIndex: 10,
          fontSize: '12px',
          fontFamily: 'monospace',
        }}
      >
        <button className="cmd-tag" onClick={() => controlsRef.current?.zoomIn()} title="Zoom In">
          [+]
        </button>
        <button className="cmd-tag" onClick={() => controlsRef.current?.zoomOut()} title="Zoom Out">
          [-]
        </button>
        <button className="cmd-tag" onClick={() => controlsRef.current?.fitView()} title="Fit Scene">
          [⛶ FIT]
        </button>
        <button className="cmd-tag" onClick={() => controlsRef.current?.resetView()} title="Reset Camera">
          [⟲ RESET]
        </button>
        <button
          className="cmd-tag"
          onClick={() => setShowOrbs(prev => !prev)}
          style={{ color: showOrbs ? '#33ff88' : '#777' }}
          title="Toggle Transaction Flow Orbs"
        >
          {showOrbs ? '[⚡ ORBS: ON]' : '[ORBS: OFF]'}
        </button>
        <button
          className="cmd-tag"
          onClick={() => setAutoRotate(prev => !prev)}
          style={{ color: autoRotate ? '#33ff88' : '#777' }}
          title="Toggle 3D Orbit Auto-Rotation"
        >
          {autoRotate ? '[⟳ ROTATE]' : '[PAUSED]'}
        </button>
      </div>

      {/* Trust & Threat Legend HUD */}
      <div
        style={{
          position: 'absolute',
          bottom: '10px',
          left: '10px',
          background: 'rgba(2, 10, 4, 0.85)',
          padding: '6px 12px',
          borderRadius: '3px',
          border: '1px solid #004d20',
          fontFamily: 'monospace',
          fontSize: '11px',
          zIndex: 10,
          display: 'flex',
          gap: '14px',
          alignItems: 'center',
        }}
      >
        <span style={{ color: '#88bb99', fontWeight: 'bold' }}>TRUST TAXONOMY:</span>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#00ff66' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00ff66', display: 'inline-block' }}></span>
          High Trust (Low Risk &lt; 0.40)
        </span>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#ffaa00' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ffaa00', display: 'inline-block' }}></span>
          Warning (0.40 - 0.75)
        </span>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#ff3344' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ff3344', display: 'inline-block' }}></span>
          Threat / Mixer (&gt; 0.75)
        </span>
        <span style={{ color: '#ffd700' }}>[TX] Block</span>
        <span style={{ color: '#00ccff' }}>[IP] Relay</span>
      </div>

      {/* Hover Node Tooltip HUD */}
      {hoveredNode && (
        <div
          style={{
            position: 'absolute',
            top: '10px',
            left: '10px',
            background: 'rgba(0, 18, 8, 0.92)',
            border: '1px solid #00ff66',
            padding: '8px 12px',
            borderRadius: '4px',
            fontFamily: 'monospace',
            fontSize: '12px',
            zIndex: 10,
            maxWidth: '380px',
            pointerEvents: 'none',
            boxShadow: '0 0 12px rgba(0, 255, 102, 0.25)',
          }}
        >
          <div style={{ color: '#00ff66', fontWeight: 'bold', borderBottom: '1px dashed #004d20', paddingBottom: '4px', marginBottom: '4px' }}>
            &gt; NODE TELEMETRY :: {hoveredNode.type}
          </div>
          <div><strong>ID:</strong> <span style={{ color: '#e0ffe8' }}>{hoveredNode.id}</span></div>
          {hoveredNode.label && <div><strong>Label:</strong> {hoveredNode.label}</div>}
          {hoveredNode.riskScore !== undefined && (
            <div>
              <strong>Risk Score:</strong>{' '}
              <span
                style={{
                  color: hoveredNode.riskScore > 0.75 ? '#ff3344' : hoveredNode.riskScore >= 0.4 ? '#ffaa00' : '#00ff66',
                  fontWeight: 'bold',
                }}
              >
                {(hoveredNode.riskScore * 100).toFixed(1)}% {hoveredNode.riskScore > 0.75 ? '[CRITICAL]' : hoveredNode.riskScore >= 0.4 ? '[SUSPICIOUS]' : '[LICIT]'}
              </span>
            </div>
          )}
          {hoveredNode.clusterId && <div><strong>CIOH Cluster:</strong> {hoveredNode.clusterId}</div>}
          <div style={{ color: '#66aa77', fontSize: '10px', marginTop: '4px' }}>Click to select &amp; view forensic details</div>
        </div>
      )}
    </div>
  );
};

export default GraphCanvas;