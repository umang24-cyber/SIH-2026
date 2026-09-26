import { useCallback, useEffect, useState } from 'react';
import { fetchObservatory } from './api';
import type { Envelope } from './types';

export type Resource<T> = {
  response: Envelope<T> | null; loading: boolean; error: string | null; retry: () => void;
};

export function useObservatoryResource<T>(path: string): Resource<T> {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<{ path: string; response: Envelope<T> | null; loading: boolean; error: string | null }>({ path, response: null, loading: true, error: null });
  const retry = useCallback(() => setAttempt(value => value + 1), []);
  useEffect(() => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 90000);
    let active = true;
    setState({ path, response: null, loading: true, error: null });
    fetchObservatory<T>(path, controller.signal).then(response => {
      if (active) setState({ path, response, loading: false, error: null });
    }).catch(error => {
      if (active) setState({ path, response: null, loading: false, error: controller.signal.aborted ? 'This section took too long to load. Please try again.' : error instanceof Error ? error.message : 'This section could not be loaded.' });
    }).finally(() => clearTimeout(timeout));
    return () => { active = false; clearTimeout(timeout); controller.abort(); };
  }, [path, attempt]);
  return { ...(state.path === path ? state : { response: null, loading: true, error: null }), retry };
}
