import type { Envelope } from './types';

export async function fetchObservatory<T>(path: string, signal: AbortSignal): Promise<Envelope<T>> {
  const response = await fetch(`/api/observatory/${path}`, { signal, headers: { Accept: 'application/json' } });
  if (!response.ok) throw new Error(`The Observatory could not be reached (HTTP ${response.status}).`);
  const body = await response.json();
  if (body.schema_version !== '1.0' || !['available', 'unavailable'].includes(body.status) || !body.meta) {
    throw new Error('The server returned an unsupported Observatory response.');
  }
  return body;
}
