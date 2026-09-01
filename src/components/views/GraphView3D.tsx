import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { ForensicNode, ForensicLink } from '../../types/terminal';

interface GraphView3DProps {
  nodes: ForensicNode[];
  links: ForensicLink[];
  highlightedNodeId?: string | null;
  onSelectNode: (nodeId: string) => void;
  onRunCommand: (cmd: string) => void;
}

export const GraphView3D: React.FC<GraphView3DProps> = ({
  nodes,
  links,
  highlightedNodeId,
  onSelectNode,
  onRunCommand
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredNode, setHoveredNode] = useState<ForensicNode | null>(null);
  const [selectedNode, setSelectedNode] = useState<ForensicNode | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // 1. Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);
    scene.fog = new THREE.FogExp2(0x000000, 0.002);

    const width = container.clientWidth;
    const height = container.clientHeight;

    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
    camera.position.set(0, 0, 220);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // 2. Node Position Simulation (3D Force Distribution)
    const nodeCount = nodes.length;
    const nodeMap = new Map<string, { node: ForensicNode; group: THREE.Group; mesh: THREE.Mesh; pos: THREE.Vector3 }>();

    // Node geometries & materials
    const boxGeo = new THREE.BoxGeometry(10, 10, 10);
    const wireGeo = new THREE.WireframeGeometry(boxGeo);

    nodes.forEach((n, i) => {
      const group = new THREE.Group();
      
      // Calculate layout coordinates in 3D sphere / cluster
      const phi = Math.acos(-1 + (2 * i) / nodeCount);
      const theta = Math.sqrt(nodeCount * Math.PI) * phi;
      const radius = 80 + (n.riskScore > 80 ? 10 : 30);
      const x = radius * Math.cos(theta) * Math.sin(phi);
      const y = radius * Math.sin(theta) * Math.sin(phi);
      const z = radius * Math.cos(phi);

      group.position.set(x, y, z);

      // Wireframe cube
      const wireMat = new THREE.LineBasicMaterial({
        color: n.riskScore >= 80 ? 0xff3344 : (n.id === highlightedNodeId ? 0x33ff88 : 0x00ff66),
        linewidth: 1
      });
      const wireframe = new THREE.LineSegments(wireGeo, wireMat);
      group.add(wireframe);

      // Inner solid core for raycasting & glow
      const coreMat = new THREE.MeshBasicMaterial({
        color: n.riskScore >= 80 ? 0x440011 : 0x00220a,
        wireframe: false,
        transparent: true,
        opacity: 0.85
      });
      const coreMesh = new THREE.Mesh(boxGeo, coreMat);
      coreMesh.userData = { nodeId: n.id };
      group.add(coreMesh);

      // Text Sprite Label
      const canvas = document.createElement('canvas');
      canvas.width = 256;
      canvas.height = 64;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, 256, 64);
        ctx.strokeStyle = n.riskScore >= 80 ? '#ff3344' : '#00ff66';
        ctx.lineWidth = 2;
        ctx.strokeRect(2, 2, 252, 60);

        ctx.font = 'bold 22px Courier New';
        ctx.fillStyle = n.riskScore >= 80 ? '#ff5566' : '#00ff66';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(`[${n.id}]`, 128, 22);

        ctx.font = '16px Courier New';
        ctx.fillStyle = '#33ff88';
        ctx.fillText(`${n.label.slice(0, 16)}`, 128, 46);
      }

      const texture = new THREE.CanvasTexture(canvas);
      const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true });
      const sprite = new THREE.Sprite(spriteMat);
      sprite.scale.set(24, 6, 1);
      sprite.position.set(0, 11, 0);
      group.add(sprite);

      scene.add(group);
      nodeMap.set(n.id, { node: n, group, mesh: coreMesh, pos: new THREE.Vector3(x, y, z) });
    });

    // 3. Links & Photon Particle Streams
    const lineMat = new THREE.LineBasicMaterial({ color: 0x005522, transparent: true, opacity: 0.6 });
    const particles: { mesh: THREE.Mesh; src: THREE.Vector3; dst: THREE.Vector3; progress: number; speed: number }[] = [];
    const particleGeo = new THREE.SphereGeometry(1.5, 6, 6);
    const particleMat = new THREE.MeshBasicMaterial({ color: 0x33ff88 });

    links.forEach(l => {
      const srcObj = nodeMap.get(l.source);
      const dstObj = nodeMap.get(l.target);
      if (srcObj && dstObj) {
        // Line link
        const points = [srcObj.pos, dstObj.pos];
        const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
        const line = new THREE.Line(lineGeo, lineMat);
        scene.add(line);

        // Animated photon particle
        const pMesh = new THREE.Mesh(particleGeo, particleMat);
        scene.add(pMesh);
        particles.push({
          mesh: pMesh,
          src: srcObj.pos,
          dst: dstObj.pos,
          progress: Math.random(),
          speed: 0.005 + Math.random() * 0.005
        });
      }
    });

    // 4. Mouse Orbit Controls (Native implementation for precision & zero extra dependencies)
    let isDragging = false;
    let isRightDragging = false;
    let previousMousePosition = { x: 0, y: 0 };
    let rotationSpeed = 0.004;

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const onMouseDown = (e: MouseEvent) => {
      if (e.button === 0) isDragging = true;
      if (e.button === 2) isRightDragging = true;
      previousMousePosition = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      if (isDragging) {
        const deltaX = e.clientX - previousMousePosition.x;
        const deltaY = e.clientY - previousMousePosition.y;

        scene.rotation.y += deltaX * rotationSpeed;
        scene.rotation.x += deltaY * rotationSpeed;
      } else if (isRightDragging) {
        const deltaX = e.clientX - previousMousePosition.x;
        const deltaY = e.clientY - previousMousePosition.y;
        camera.position.x -= deltaX * 0.2;
        camera.position.y += deltaY * 0.2;
      }

      previousMousePosition = { x: e.clientX, y: e.clientY };

      // Raycast for hover
      raycaster.setFromCamera(mouse, camera);
      const meshes = Array.from(nodeMap.values()).map(v => v.mesh);
      const intersects = raycaster.intersectObjects(meshes);

      if (intersects.length > 0) {
        const hitNodeId = intersects[0].object.userData.nodeId;
        const n = nodes.find(item => item.id === hitNodeId) || null;
        setHoveredNode(n);
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
      const meshes = Array.from(nodeMap.values()).map(v => v.mesh);
      const intersects = raycaster.intersectObjects(meshes);

      if (intersects.length > 0) {
        const hitNodeId = intersects[0].object.userData.nodeId;
        const n = nodes.find(item => item.id === hitNodeId) || null;
        setSelectedNode(n);
        if (n) {
          onSelectNode(n.id);
        }
      }
    };

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      camera.position.z += e.deltaY * 0.15;
      camera.position.z = Math.max(40, Math.min(450, camera.position.z));
    };

    const domEl = renderer.domElement;
    domEl.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    domEl.addEventListener('click', onClick);
    domEl.addEventListener('wheel', onWheel, { passive: false });
    domEl.addEventListener('contextmenu', e => e.preventDefault());

    // 5. Animation Loop
    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      // Auto gentle idle drift if not user dragging
      if (!isDragging && !isRightDragging) {
        scene.rotation.y += 0.001;
      }

      // Animate photon particles along directed links
      particles.forEach(p => {
        p.progress += p.speed;
        if (p.progress > 1) p.progress = 0;
        p.mesh.position.lerpVectors(p.src, p.dst, p.progress);
      });

      // Animate node cube pulse
      nodeMap.forEach(({ group, node }) => {
        if (node.riskScore >= 80) {
          const s = 1 + Math.sin(Date.now() * 0.004) * 0.08;
          group.scale.set(s, s, s);
        }
      });

      renderer.render(scene, camera);
    };
    animate();

    // Resize handler
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      domEl.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      domEl.removeEventListener('click', onClick);
      domEl.removeEventListener('wheel', onWheel);
      window.removeEventListener('resize', handleResize);
      if (container.contains(domEl)) {
        container.removeChild(domEl);
      }
      renderer.dispose();
    };
  }, [nodes, links, highlightedNodeId]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', minHeight: '340px' }}>
      {/* 3D WebGL Canvas Container */}
      <div ref={containerRef} style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }} />

      {/* Top Left Graph HUD Overlay */}
      <div style={{ position: 'absolute', top: 8, left: 10, background: 'rgba(0, 16, 6, 0.85)', border: '1px solid #007a33', padding: '8px 12px', fontSize: '13px', pointerEvents: 'none', zIndex: 5 }}>
        <div style={{ color: '#33ff88', fontWeight: 'bold', marginBottom: '2px' }}>
          3D FORCE GRAPH RENDERER :: ACTIVE
        </div>
        <div style={{ color: '#00ff66' }}>
          NODES: {nodes.length} | LINKS: {links.length} | ENGINE: THREE.js WebGL
        </div>
        <div style={{ color: '#007a33', marginTop: '2px' }}>
          Controls: [Drag] Rotate | [Right-Drag] Pan | [Scroll] Zoom | [Click] Select
        </div>
      </div>

      {/* Node Telemetry Card Overlay (Hover or Selected) */}
      {(hoveredNode || selectedNode) && (
        <div style={{ position: 'absolute', bottom: 12, right: 12, width: '320px', background: 'rgba(0, 14, 5, 0.95)', border: '1px solid #00ff66', padding: '12px', zIndex: 10, fontSize: '14px' }}>
          {(() => {
            const active = hoveredNode || selectedNode!;
            return (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed #007a33', paddingBottom: '4px', marginBottom: '6px' }}>
                  <strong style={{ color: '#33ff88' }}>[{active.id}]</strong>
                  <span style={{ color: active.riskScore >= 80 ? '#ff3344' : '#00ff66', fontWeight: 'bold' }}>
                    RISK: {active.riskScore}/100
                  </span>
                </div>
                <p><strong>LABEL:</strong> {active.label}</p>
                <p><strong>TYPE:</strong> {active.type}</p>
                <p><strong>CLUSTER:</strong> {active.clusterId}</p>
                <p><strong>BALANCE:</strong> {active.balanceEth} ETH</p>
                <p><strong>TRANSACTIONS:</strong> {active.txCount}</p>
                <div style={{ marginTop: '8px', borderTop: '1px dashed #007a33', paddingTop: '6px', display: 'flex', gap: '8px' }}>
                  <span
                    className="cmd-clickable"
                    style={{ fontSize: '13px' }}
                    onClick={() => onRunCommand(`inspect ${active.id}`)}
                  >
                    &gt; inspect {active.id}
                  </span>
                  <span
                    className="cmd-clickable"
                    style={{ fontSize: '13px' }}
                    onClick={() => onRunCommand(`trace ${active.id} 0xEE3388A1`)}
                  >
                    &gt; trace to OTC
                  </span>
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
};
