import { useId, useMemo, useState, type CSSProperties } from 'react';
import type { Diagram } from '../types';
import { useReveal } from '../../motion/useReveal';

export function DirectedDiagram({ diagram, compact = false }: { diagram: Diagram; compact?: boolean }) {
  const reveal = useReveal(diagram.id, 1600, true);
  const [selected, setSelected] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const marker = `arrow${useId().replace(/:/g, '')}`;
  const layout = useMemo(() => {
    // Longest-path ranks keep every supplied direction, including support branches.
    const ranks = new Map(diagram.nodes.map(node => [node.id, 0]));
    for (let i = 0; i < diagram.nodes.length; i++) {
      let changed = false;
      diagram.edges.forEach(edge => {
        const rank = Math.min(diagram.nodes.length - 1, (ranks.get(edge.source) || 0) + 1);
        if (rank > (ranks.get(edge.target) || 0)) { ranks.set(edge.target, rank); changed = true; }
      });
      if (!changed) break;
    }
    const levels = Math.max(...ranks.values()) + 1;
    const width = compact ? 620 : 1140;
    const height = compact ? 290 : 650;
    const nodeWidth = compact ? 142 : 130;
    const nodeHeight = compact ? 56 : 70;
    const positions = new Map<string, { x: number; y: number }>();
    for (let level = 0; level < levels; level++) {
      const nodes = diagram.nodes.filter(node => ranks.get(node.id) === level);
      nodes.forEach((node, i) => positions.set(node.id, { x: 24 + level / Math.max(levels - 1, 1) * (width - nodeWidth - 48), y: (i + 1) / (nodes.length + 1) * height - nodeHeight / 2 }));
    }
    return { width, height, nodeWidth, nodeHeight, positions, ranks, levels };
  }, [diagram, compact]);
  const node = diagram.nodes.find(node => node.id === selected);
  const edge = diagram.edges.find(edge => edge.id === selected);
  const { width, height, nodeWidth, nodeHeight, positions } = layout;
  return <div ref={reveal.ref} data-reveal={reveal.phase} onFocusCapture={reveal.showNow} className={`obs-diagram${compact ? ' obs-diagram-compact' : ''}`}>
    {!compact && <div className="obs-diagram-toolbar"><span className="eyebrow">Select a stage to follow the logic</span><div><button aria-label="Zoom out diagram" disabled={zoom <= 1} onClick={() => setZoom(value => Math.max(1, value - .25))}>−</button><button aria-label="Reset diagram zoom" onClick={() => setZoom(1)}>{Math.round(zoom * 100)}%</button><button aria-label="Zoom in diagram" disabled={zoom >= 2} onClick={() => setZoom(value => Math.min(2, value + .25))}>+</button></div></div>}
    <div className="obs-diagram-viewport" tabIndex={0} aria-label={`${diagram.label} diagram viewport`}>
      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: `${zoom * 100}%`, minWidth: compact ? 380 : 800 }} role="group" aria-label={diagram.label}>
        <defs><marker id={marker} markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="context-stroke" /></marker></defs>
        {diagram.edges.map(connection => {
          const from = positions.get(connection.source), to = positions.get(connection.target);
          if (!from || !to) return null;
          const sx = from.x + nodeWidth, sy = from.y + nodeHeight / 2, tx = to.x - 5, ty = to.y + nodeHeight / 2;
          const d = `M${sx},${sy} C${sx + (tx - sx) * .48},${sy} ${tx - (tx - sx) * .48},${ty} ${tx},${ty}`;
          const active = selected === connection.id || selected === connection.source || selected === connection.target;
          return <g key={connection.id} role="button" tabIndex={0} aria-label={`${connection.label}: ${diagram.nodes.find(n => n.id === connection.source)?.label} to ${diagram.nodes.find(n => n.id === connection.target)?.label}`} aria-pressed={selected === connection.id} onClick={() => setSelected(connection.id)} onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); setSelected(connection.id); } }}>
            <path d={d} fill="none" stroke="transparent" strokeWidth="18" className="obs-edge-hit" />
            <path className="reveal-edge" pathLength={1} style={{ '--reveal-delay': `${(layout.ranks.get(connection.source) || 0) / Math.max(layout.levels - 1, 1) * 900 + 170}ms` } as CSSProperties} d={d} fill="none" stroke={active ? 'var(--wine)' : 'var(--olive)'} strokeWidth={active ? 2.5 : 1.3} opacity={selected && !active ? .3 : .8} markerEnd={`url(#${marker})`} pointerEvents="none" />
            <title>{connection.label}</title>
          </g>;
        })}
        {diagram.nodes.map((entry, index) => {
          const position = positions.get(entry.id)!;
          const words = entry.label.split(' '), lines: string[] = [];
          words.forEach(word => { if (!lines.length || lines[lines.length - 1].length + word.length > 17) lines.push(word); else lines[lines.length - 1] += ` ${word}`; });
          return <g key={entry.id} transform={`translate(${position.x},${position.y})`} role="button" tabIndex={0} aria-label={entry.label} aria-pressed={selected === entry.id} onClick={() => setSelected(entry.id)} onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); setSelected(entry.id); } }} className="obs-diagram-node">
            <g className="reveal-node" style={{ '--reveal-delay': `${(layout.ranks.get(entry.id) || 0) / Math.max(layout.levels - 1, 1) * 900}ms` } as CSSProperties}><rect width={nodeWidth} height={nodeHeight} fill={selected === entry.id ? 'var(--olive)' : 'var(--paper-light)'} stroke={selected === entry.id ? 'var(--olive)' : 'var(--rule)'} />
            <text x="9" y="13" className="obs-node-number" fill={selected === entry.id ? '#d9d1c2' : 'var(--muted)'}>{String(index + 1).padStart(2, '0')}</text>
            <text textAnchor="middle" fill={selected === entry.id ? 'var(--paper-light)' : 'var(--ink)'}>{lines.map((line, i) => <tspan key={i} x={nodeWidth / 2} y={nodeHeight / 2 + (i - (lines.length - 1) / 2) * 14 + 8}>{line}</tspan>)}</text></g>
          </g>;
        })}
      </svg>
    </div>
    <div className="obs-diagram-detail" aria-live="polite"><strong>{node?.label || edge?.label || (compact ? 'An illustrative structure' : 'A scenario, from source to dossier')}</strong><p>{node?.description || (edge ? `${diagram.nodes.find(n => n.id === edge.source)?.label} → ${diagram.nodes.find(n => n.id === edge.target)?.label}` : diagram.description)}</p>{selected && <button onClick={() => setSelected(null)}>Clear selection</button>}</div>
    {!compact && <details className="obs-data-table"><summary>Read all stages & connections</summary><ol>{diagram.nodes.map(node => <li key={node.id}><strong>{node.label}.</strong> {node.description}</li>)}</ol><ul>{diagram.edges.map(edge => <li key={edge.id}>{diagram.nodes.find(n => n.id === edge.source)?.label} → {diagram.nodes.find(n => n.id === edge.target)?.label}: {edge.label}</li>)}</ul></details>}
  </div>;
}
