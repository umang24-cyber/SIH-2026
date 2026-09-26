import { useId, useState, type CSSProperties } from 'react';
import type { Dataset } from '../types';
import { date, number, percent } from './SectionState';
import { useReveal } from '../../motion/useReveal';
import { ScrambleNumber } from '../../motion/ScrambleNumber';

type Bar = { id: string; label: string; value: number };
export function Bars({ items, ratio = false, label, scaleToOne = false }: { items: Bar[]; ratio?: boolean; label: string; scaleToOne?: boolean }) {
  const reveal = useReveal(JSON.stringify(items), 1250, true);
  const max = scaleToOne ? 1 : Math.max(...items.map(item => item.value), 0.00001);
  const format = ratio ? percent : number;
  return <div ref={reveal.ref} data-reveal={reveal.phase} className="obs-bars" role="list" aria-label={label}>{items.length ? items.map((item, index) => <div className="obs-bar" role="listitem" key={item.id} style={{ '--reveal-delay': `${Math.min(index * 40, 480)}ms` } as CSSProperties}>
    <div className="obs-bar-caption"><span>{item.label}</span><strong><ScrambleNumber value={format(item.value)} /></strong></div>
    <div className="obs-bar-track"><span className="reveal-bar" style={{ width: `${item.value / max * 100}%`, background: index % 3 === 1 ? 'var(--wine)' : index % 3 === 2 ? 'var(--brass)' : 'var(--olive)' }} /></div>
  </div>) : <p>No observations are available.</p>}</div>;
}

export function Timeline({ dataset, volume }: { dataset: Dataset; volume: boolean }) {
  const reveal = useReveal<HTMLElement>(`${dataset.bucket}:${volume}:${JSON.stringify(dataset.timeline)}`, 1150, true);
  const [selected, setSelected] = useState<number | null>(null);
  const id = useId().replace(/:/g, '');
  const points = dataset.timeline;
  const values = points.map(point => volume ? point.output_volume_btc : point.transactions);
  const max = Math.max(...values, 1);
  const width = 840, height = 280, left = 66, right = 22, top = 20, bottom = 40;
  const x = (index: number) => left + index / Math.max(points.length - 1, 1) * (width - left - right);
  const y = (value: number) => height - bottom - value / max * (height - top - bottom);
  const line = values.map((value, i) => `${i ? 'L' : 'M'}${x(i)},${y(value)}`).join(' ');
  const active = selected !== null ? Math.min(selected, points.length - 1) : points.length - 1;
  const format = (value: number) => volume ? new Intl.NumberFormat('en-US', { maximumFractionDigits: 8 }).format(value) : number(value);
  const nearest = (event: React.PointerEvent<SVGSVGElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const px = (event.clientX - rect.left) / rect.width * width;
    setSelected(Math.max(0, Math.min(points.length - 1, Math.round((px - left) / (width - left - right) * (points.length - 1)))));
  };
  if (!points.length) return <p>No timeline observations available.</p>;
  return <figure ref={reveal.ref} data-reveal={reveal.phase} className="obs-timeline" onFocusCapture={reveal.showNow}>
    <div className="obs-chart-readout" aria-live="polite"><span>{date(points[active].timestamp)} · UTC bucket start</span><strong>{format(values[active])} <small>{volume ? 'BTC' : 'transactions'}</small></strong></div>
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${volume ? 'Transaction output volume in BTC' : 'Transaction count'} over time. Exact values are available in the bucket selector and data table.`} onPointerMove={nearest} onPointerDown={nearest}>
      <defs><linearGradient id={id} x1="0" y1="0" x2="0" y2="1"><stop stopColor="#46513b" stopOpacity=".22" /><stop offset="1" stopColor="#46513b" stopOpacity=".015" /></linearGradient></defs>
      {[0, .25, .5, .75, 1].map(tick => <g key={tick}><line x1={left} x2={width - right} y1={y(max * tick)} y2={y(max * tick)} stroke="var(--rule)" strokeDasharray={tick ? '3 5' : undefined} /><text x={left - 10} y={y(max * tick) + 4} textAnchor="end">{new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(max * tick)}</text></g>)}
      <g className="reveal-plot"><path d={`${line} L${x(points.length - 1)},${height - bottom} L${left},${height - bottom} Z`} fill={`url(#${id})`} />
      <path className="reveal-line" pathLength={1} d={line} fill="none" stroke="var(--olive)" strokeWidth="2.5" strokeLinejoin="round" /></g>
      <line x1={x(active)} x2={x(active)} y1={top} y2={height - bottom} stroke="var(--wine)" strokeDasharray="3 4" />
      <circle cx={x(active)} cy={y(values[active])} r="5" fill="var(--wine)" stroke="var(--paper)" strokeWidth="2" />
      {[0, ...(points.length > 2 ? [Math.floor((points.length - 1) / 2)] : []), ...(points.length > 1 ? [points.length - 1] : [])].map(index => <text key={index} x={x(index)} y={height - 10} textAnchor={index === 0 ? 'start' : index === points.length - 1 ? 'end' : 'middle'}>{date(points[index].timestamp)}</text>)}
    </svg>
    <label className="obs-scrubber">Explore a time bucket<input aria-label="Explore a time bucket" type="range" min="0" max={points.length - 1} value={active} onChange={event => setSelected(Number(event.target.value))} /></label>
    <figcaption>Fig. 01 — {volume ? 'Transaction output volume (BTC), including change and repeated transfers.' : 'Transaction activity in the bundled train and test ledger.'} All dates are UTC.</figcaption>
    <details className="obs-data-table"><summary>View timeline data</summary><div tabIndex={0} className="obs-table-scroll"><table><caption>Timeline · {dataset.bucket} · UTC</caption><thead><tr><th>Bucket start</th><th>Transactions</th><th>Output volume (BTC)</th></tr></thead><tbody>{points.map(point => <tr key={point.timestamp}><th>{date(point.timestamp)}</th><td>{number(point.transactions)}</td><td>{new Intl.NumberFormat('en-US', { maximumFractionDigits: 8 }).format(point.output_volume_btc)}</td></tr>)}</tbody></table></div></details>
  </figure>;
}
