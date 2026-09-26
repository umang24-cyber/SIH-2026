import type { ReactNode } from 'react';
import type { Resource } from '../useObservatoryResource';
import type { Meta } from '../types';

export const number = (value: number) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value);
export const percent = (value: number) => new Intl.NumberFormat('en-US', { style: 'percent', maximumFractionDigits: 2 }).format(value);
export const date = (value: string) => new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(value));

export function SourceNote({ meta }: { meta: Meta }) {
  return <details className="obs-source"><summary>Sources & methodology <span aria-hidden="true">+</span></summary>
    <p>{meta.scope.replace(/_/g, ' ')} · {meta.dataset_version || 'Architecture / illustration'}{meta.model_version ? ` · Model ${meta.model_version.toUpperCase()}` : ''}</p>
    <ul>{meta.notes.map(note => <li key={note}>{note}</li>)}</ul>
    <ul className="obs-source-files">{meta.sources.map(source => <li key={source}>{source}</li>)}</ul>
    <p>Response generated {date(meta.generated_at)} (UTC). This is not the evaluation date.</p>
  </details>;
}

export function SectionState<T>({ resource, label, children }: { resource: Resource<T>; label: string; children: (data: T, meta: Meta) => ReactNode }) {
  if (resource.loading) return <div className="obs-loading" role="status" aria-label={`Loading ${label}`}><span className="eyebrow">Preparing {label}</span><div /><div /><div /></div>;
  const { response, error } = resource;
  if (error || response?.status !== 'available' || !response.data) return <div className="obs-unavailable" role="status"><span className="eyebrow">A note from the data desk</span><h3>{label} is unavailable.</h3><p>{error || response?.message || 'No compatible local artifact is available for this section.'}</p><button onClick={resource.retry}>Retry this section <span aria-hidden="true">↗</span></button></div>;
  return <>{children(response.data, response.meta)}<SourceNote meta={response.meta} /></>;
}
