import { createContext, useContext, useEffect, useRef, useState } from 'react';
import { publicAudio } from '../audio/publicAudio';

export const MotionReadyContext = createContext(true);
export function useReducedMotion() {
  const [reduced, setReduced] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => { const media = window.matchMedia('(prefers-reduced-motion: reduce)'); const update = () => setReduced(media.matches); media.addEventListener('change', update); return () => media.removeEventListener('change', update); }, []);
  return reduced;
}

export function useReveal<T extends Element = HTMLDivElement>(key: string, duration = 1000, audible = false) {
  const ref = useRef<T>(null);
  const ready = useContext(MotionReadyContext);
  const reduced = useReducedMotion();
  const [state, setState] = useState({ key, phase: 'waiting' });
  const completed = useRef<string | null>(null);
  const stop = useRef<() => void>(() => {});
  const showNow = () => { completed.current = key; stop.current(); setState({ key, phase: 'done' }); };
  useEffect(() => {
    if (reduced || completed.current === key) { completed.current = key; setState({ key, phase: 'done' }); return; }
    setState({ key, phase: 'waiting' });
    if (!ready || !ref.current) return;
    let timer = 0, started = false;
    let stopAudio = () => {};
    const finish = () => { clearTimeout(timer); stopAudio(); completed.current = key; setState({ key, phase: 'done' }); };
    const start = () => {
      if (started || document.hidden) return;
      started = true; observer.disconnect(); setState({ key, phase: 'playing' });
      if (audible) stopAudio = publicAudio.sequence('chart', [{ at: 0, type: 'chart' }], duration);
      timer = window.setTimeout(finish, duration);
    };
    const observer = new IntersectionObserver(entries => { if (entries.some(entry => entry.isIntersecting)) start(); }, { threshold: .08 });
    observer.observe(ref.current);
    const visibility = () => { if (document.hidden && started) finish(); else if (!document.hidden && !started && ref.current) { observer.unobserve(ref.current); observer.observe(ref.current); } };
    document.addEventListener('visibilitychange', visibility);
    stop.current = finish;
    return () => { observer.disconnect(); clearTimeout(timer); stopAudio(); document.removeEventListener('visibilitychange', visibility); stop.current = () => {}; };
  }, [key, duration, audible, ready, reduced]);
  return { ref, phase: reduced ? 'done' : state.key === key ? state.phase : 'waiting', reduced, showNow };
}
