import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import './NewspaperEntrance.css';
import { publicAudio } from '../../audio/publicAudio';

const clamp = (value: number) => Math.max(0, Math.min(1, value));
const smooth = (value: number) => { const t = clamp(value); return t * t * (3 - 2 * t); };

/** Typeset the visible HTML edition onto the sheet, using its actual text and layout.
 * This stays local and keeps the last 3D frame aligned with the accessible page.
 */
function printEdition(width: number, height: number) {
  const canvas = document.createElement('canvas');
  const density = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(width * density);
  canvas.height = Math.round(height * density);
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('Paper texture is unavailable');
  ctx.scale(density, density);
  ctx.fillStyle = '#f5f1e8'; ctx.fillRect(0, 0, width, height);
  const paper = document.querySelector<HTMLElement>('.obs-paper');
  if (!paper) throw new Error('The reading surface is not ready');
  const origin = paper.getBoundingClientRect().left;
  const visible = (rect: DOMRect) => rect.width > 0 && rect.height > 0 && rect.top < height && rect.bottom > 0;
  paper.querySelectorAll<HTMLElement>('*').forEach(element => {
    if (element.closest('svg, .obs-seal, .sr-only, [data-reveal="waiting"]')) return;
    const rect = element.getBoundingClientRect();
    if (!visible(rect)) return;
    const style = getComputedStyle(element);
    if (style.backgroundColor !== 'rgba(0, 0, 0, 0)') { ctx.fillStyle = style.backgroundColor; ctx.fillRect(rect.left - origin, rect.top, rect.width, rect.height); }
    const sides = [
      [style.borderTopWidth, style.borderTopColor, style.borderTopStyle, rect.left - origin, rect.top, rect.right - origin, rect.top],
      [style.borderBottomWidth, style.borderBottomColor, style.borderBottomStyle, rect.left - origin, rect.bottom, rect.right - origin, rect.bottom],
      [style.borderLeftWidth, style.borderLeftColor, style.borderLeftStyle, rect.left - origin, rect.top, rect.left - origin, rect.bottom],
      [style.borderRightWidth, style.borderRightColor, style.borderRightStyle, rect.right - origin, rect.top, rect.right - origin, rect.bottom],
    ] as const;
    sides.forEach(([size, color, kind, x1, y1, x2, y2]) => {
      const thickness = parseFloat(size);
      if (!thickness) return;
      ctx.strokeStyle = color; ctx.lineWidth = kind === 'double' ? 1 : thickness;
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
      if (kind === 'double') { ctx.beginPath(); ctx.moveTo(x1, y1 - thickness + 1); ctx.lineTo(x2, y2 - thickness + 1); ctx.stroke(); }
    });
  });
  const walker = document.createTreeWalker(paper, NodeFilter.SHOW_TEXT);
  const range = document.createRange();
  let node: Node | null;
  while ((node = walker.nextNode())) {
    const parent = node.parentElement;
    if (!parent || !node.textContent?.trim() || parent.closest('svg, .obs-seal, .sr-only, [data-reveal="waiting"]')) continue;
    if (!visible(parent.getBoundingClientRect())) continue;
    const style = getComputedStyle(parent);
    if (style.visibility === 'hidden' || style.display === 'none') continue;
    ctx.font = `${style.fontStyle} ${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
    ctx.fillStyle = style.color;
    (ctx as CanvasRenderingContext2D & { letterSpacing: string }).letterSpacing = style.letterSpacing === 'normal' ? '0px' : style.letterSpacing;
    const text = node.textContent;
    for (const match of text.matchAll(/\S+/g)) {
      const start = match.index!;
      range.setStart(node, start); range.setEnd(node, start + match[0].length);
      const rect = range.getBoundingClientRect();
      if (!visible(rect)) continue;
      const value = style.textTransform === 'uppercase' ? match[0].toUpperCase() : match[0];
      const ascent = ctx.measureText(value).fontBoundingBoxAscent;
      ctx.fillText(value, rect.left - origin, rect.top + ascent);
    }
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  return texture;
}

/** A short-lived curled sheet. The accessible reading surface remains ordinary HTML. */
export function NewspaperEntrance({ onComplete }: { onComplete: () => void }) {
  const stage = useRef<HTMLDivElement>(null);
  const canvasHost = useRef<HTMLDivElement>(null);
  const skip = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    let disposed = false, frame = 0;
    let stopSound = () => {};
    let renderer: THREE.WebGLRenderer | undefined;
    const resources: { dispose: () => void }[] = [];
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const finish = () => { if (!disposed) onComplete(); };
    const key = (event: KeyboardEvent) => { if (event.key === 'Escape') { event.preventDefault(); finish(); } };
    const changed = () => { if (preference.matches) finish(); };
    const contextLost = (event: Event) => { event.preventDefault(); finish(); };
    const onHidden = () => { if (document.hidden) finish(); };
    skip.current?.focus({ preventScroll: true });
    window.addEventListener('keydown', key);
    window.addEventListener('resize', finish);
    preference.addEventListener('change', changed);
    document.addEventListener('visibilitychange', onHidden);
    const fallback = window.setTimeout(finish, 3200);
    if (preference.matches) finish();
    else try {
      const width = window.innerWidth, height = window.innerHeight;
      const paperWidth = Math.min(width, 1600), paperHeight = height;
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.6));
      renderer.setSize(width, height);
      renderer.setClearColor(0x000000, 0);
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.domElement.setAttribute('aria-hidden', 'true');
      renderer.domElement.addEventListener('webglcontextlost', contextLost);
      canvasHost.current?.appendChild(renderer.domElement);
      const scene = new THREE.Scene();
      const camera = new THREE.OrthographicCamera(-width / 2, width / 2, height / 2, -height / 2, .1, 10000);
      camera.position.z = 3000;
      const ambient = new THREE.AmbientLight(0xffffff, 1.5); scene.add(ambient);
      const light = new THREE.DirectionalLight(0xfff5dd, 2.3);
      light.position.set(-width, height, 1800); scene.add(light);
      const group = new THREE.Group(); scene.add(group);
      const texture = printEdition(paperWidth, paperHeight); resources.push(texture);
      const material = new THREE.MeshStandardMaterial({ map: texture, emissiveMap: texture, emissive: 0xffffff, emissiveIntensity: 0, side: THREE.DoubleSide, roughness: 1, metalness: 0 }); resources.push(material);
      const sheets: THREE.PlaneGeometry[] = [];
      for (let layer = 2; layer >= 0; layer--) {
        const geometry = new THREE.PlaneGeometry(paperWidth, paperHeight, 2, 150); resources.push(geometry); sheets.push(geometry);
        const back = layer ? new THREE.MeshStandardMaterial({ color: layer === 2 ? '#d9d1c2' : '#e9e3d6', roughness: 1, side: THREE.DoubleSide }) : material;
        if (layer) resources.push(back);
        const sheet = new THREE.Mesh(geometry, back); sheet.position.z = -layer * 1.7; group.add(sheet);
      }
      const shadowCanvas = document.createElement('canvas'); shadowCanvas.width = 128; shadowCanvas.height = 128;
      const ctx = shadowCanvas.getContext('2d')!;
      const gradient = ctx.createRadialGradient(64, 64, 0, 64, 64, 64); gradient.addColorStop(0, '#25282070'); gradient.addColorStop(1, '#25282000'); ctx.fillStyle = gradient; ctx.fillRect(0, 0, 128, 128);
      const shadowTexture = new THREE.CanvasTexture(shadowCanvas); resources.push(shadowTexture);
      const shadowMaterial = new THREE.MeshBasicMaterial({ map: shadowTexture, transparent: true, depthWrite: false }); resources.push(shadowMaterial);
      const shadowGeometry = new THREE.PlaneGeometry(paperWidth * 1.2, paperHeight * .45); resources.push(shadowGeometry);
      const shadow = new THREE.Mesh(shadowGeometry, shadowMaterial); shadow.position.z = -100; scene.add(shadow);
      const started = performance.now();
      stopSound = publicAudio.sequence('newspaper', [{ at: 0, type: 'delivery' }, { at: 850, type: 'unroll' }], 2450);
      let refreshed = false;
      const animate = (now: number) => {
        if (disposed) return;
        const elapsed = now - started;
        const flight = 1 - Math.pow(1 - clamp(elapsed / 800), 3);
        const open = smooth((elapsed - 850) / 1300);
        const settle = smooth((elapsed - 1800) / 450);
        if (!refreshed && elapsed >= 1750) {
          // Refresh once with any newly arrived API data before the HTML handoff.
          const finalTexture = printEdition(paperWidth, paperHeight); resources.push(finalTexture);
          material.map = finalTexture; material.emissiveMap = finalTexture; material.needsUpdate = true;
          refreshed = true;
        }
        ambient.intensity = 1.5 * (1 - settle); light.intensity = 1.5 * (1 - settle);
        material.emissiveIntensity = settle;
        const flat = paperHeight * open;
        const radius = Math.max(22, paperHeight * .115 * (1 - open));
        sheets.forEach(geometry => {
          const position = geometry.attributes.position;
          for (let i = 0; i < position.count; i++) {
            const row = Math.floor(i / 3);
            const distance = paperHeight * (1 - row / 150);
            const remaining = Math.max(0, distance - flat);
            const angle = remaining / radius;
            const y = -paperHeight / 2 + Math.min(distance, flat) + Math.sin(angle) * radius;
            const z = (1 - Math.cos(angle)) * radius;
            position.setY(i, y); position.setZ(i, z);
          }
          position.needsUpdate = true; geometry.computeVertexNormals();
        });
        const bounce = elapsed > 620 && elapsed < 1000 ? Math.sin((elapsed - 620) / 380 * Math.PI) * 20 : 0;
        group.position.set((-width * .95) * (1 - flight), height * .8 * (1 - flight) + paperHeight / 2 * (1 - open) + bounce, 0);
        group.rotation.set((.65 * (1 - flight) + .12 * (1 - open)) * (1 - settle), -.35 * (1 - flight), (-.7 * (1 - flight) + .055 * (1 - open)));
        const scale = (.32 + .33 * flight) + .35 * open;
        group.scale.setScalar(scale);
        shadow.position.x = group.position.x + 25; shadow.position.y = group.position.y - paperHeight / 2 * (1 - open) - 15;
        shadow.scale.set(1, .65 + open * 2, 1); shadowMaterial.opacity = flight * (1 - settle);
        const reveal = smooth((elapsed - 2150) / 300);
        if (stage.current) stage.current.style.opacity = String(1 - reveal);
        renderer!.render(scene, camera);
        if (elapsed >= 2450) finish(); else frame = requestAnimationFrame(animate);
      };
      frame = requestAnimationFrame(animate);
    } catch { finish(); }
    return () => {
      disposed = true; cancelAnimationFrame(frame); clearTimeout(fallback);
      stopSound(); document.removeEventListener('visibilitychange', onHidden);
      window.removeEventListener('keydown', key); window.removeEventListener('resize', finish);
      preference.removeEventListener('change', changed);
      if (renderer) { renderer.domElement.removeEventListener('webglcontextlost', contextLost); renderer.dispose(); renderer.forceContextLoss(); renderer.domElement.remove(); }
      resources.forEach(resource => resource.dispose());
    };
  }, [onComplete]);
  return <div className="editorial newspaper-entrance" ref={stage}><div className="newspaper-canvas" ref={canvasHost} /><div className="newspaper-controls"><span role="status">Delivering the Observatory</span><button ref={skip} onClick={onComplete}>Skip opening ↗</button></div></div>;
}
