import { useCallback, useEffect, useRef, useState } from 'react';
import type { KeyboardEvent, MouseEvent as ReactMouseEvent, PointerEvent as ReactPointerEvent } from 'react';

export type ArtworkId = 'wine' | 'coin' | 'fern' | 'fern-low';
export interface LiquidRow { start: number; end: number }

const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));
const freshBody = () => ({ value: 0, velocity: 0, target: 0, hover: 0 });

/** One clock owns both ambient motion and gesture physics. React only handles UI state. */
export function useLandingMotion(isExiting: boolean, liquidMask: LiquidRow[]) {
  const sceneRef = useRef<HTMLDivElement>(null);
  const [paused, setPaused] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(() =>
    window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const state = useRef({
    wine: freshBody(), coin: freshBody(), fern: freshBody(), 'fern-low': freshBody(),
    time: 0, liquid: 0, liquidVelocity: 0, ripple: 0,
  });
  const drag = useRef<{
    id: ArtworkId; pointerId: number; element: HTMLButtonElement;
    startX: number; startValue: number; lastX: number; lastTime: number; scale: number;
  } | null>(null);
  const drawRef = useRef<() => void>(() => {});
  const suppressClick = useRef(false);

  const release = useCallback(() => {
    const current = drag.current;
    if (!current) return;
    drag.current = null;
    current.element.removeAttribute('data-dragging');
    if (current.element.hasPointerCapture(current.pointerId)) {
      current.element.releasePointerCapture(current.pointerId);
    }
    state.current[current.id].target = 0;
  }, []);

  useEffect(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const change = () => setReducedMotion(preference.matches);
    preference.addEventListener('change', change);
    return () => preference.removeEventListener('change', change);
  }, []);

  useEffect(() => {
    const root = sceneRef.current;
    if (!root) return;
    release();
    const ids: ArtworkId[] = ['wine', 'coin', 'fern', 'fern-low'];
    const poses = Object.fromEntries(ids.map(id => [id,
      root.querySelector<HTMLElement>(`[data-motion-pose="${id}"]`)!])) as Record<ArtworkId, HTMLElement>;
    const bands = {
      fern: Array.from(poses.fern.querySelectorAll<HTMLElement>('.landing-fern-band')),
      'fern-low': Array.from(poses['fern-low'].querySelectorAll<HTMLElement>('.landing-fern-band')),
    };
    const liquidRows = Array.from(root.querySelectorAll<HTMLElement>('[data-liquid-row]')).map(row => ({
      padding: row.children[0] as HTMLElement, fill: row.children[1] as HTMLElement,
    }));
    let frame = 0;
    let last = 0;
    let lastLiquid = -Infinity;
    const ambient = !paused && !reducedMotion;

    const draw = (forceLiquid = false) => {
      const s = state.current;
      poses.wine.style.transform = `rotate(${s.wine.value}deg)`;
      poses.coin.style.transform = `rotateY(${s.coin.value % 360}deg)`;
      poses.coin.style.setProperty('--coin-light', `${0.86 + 0.14 * Math.abs(Math.cos(s.coin.value * Math.PI / 180))}`);
      poses.coin.parentElement!.style.transform = `rotateX(${s.coin.hover * 0.3}deg)`;
      (['fern', 'fern-low'] as const).forEach((id, index) => {
        bands[id].forEach((band, bandIndex) => {
          const weight = 1 - bandIndex / (bands[id].length - 1);
          const breeze = !reducedMotion ? Math.sin(s.time * 0.95 - bandIndex * 0.12 + index * 2.3) * 3 : 0;
          band.style.transform = `translateX(${(s[id].value + breeze) * weight * weight}px)`;
        });
      });
      if (forceLiquid || s.time - lastLiquid >= 1 / 24) {
        lastLiquid = s.time;
        liquidRows.forEach(({ padding, fill }, row) => {
          const mask = liquidMask[row];
          let first = -1;
          let text = '';
          for (let column = mask.start; column < mask.end; column++) {
            // Character aspect ratio converts glass rotation to a level world-space surface.
            const surface = 16 - (column - 25) * Math.tan(s.liquid * Math.PI / 180) * 0.566
              + (!reducedMotion ? Math.sin(column * 0.3 + s.time * 1.7) * (0.32 + s.ripple) : 0);
            if (row >= surface) {
              if (first < 0) first = column;
              const shimmer = Math.sin(column * 0.45 + row * 0.8 + s.time * 1.4);
              text += row - surface < 1 ? '~' : shimmer > 0.4 ? ';' : ':';
            } else if (first >= 0) {
              text += ' ';
            }
          }
          padding.textContent = ' '.repeat(Math.max(0, first));
          fill.textContent = text.trimEnd();
        });
      }
    };
    drawRef.current = () => draw(true);

    const tick = (now: number) => {
      const dt = last ? Math.min((now - last) / 1000, 1 / 30) : 1 / 60;
      last = now;
      const s = state.current;
      s.time += dt;
      for (const id of ['wine', 'fern', 'fern-low'] as const) {
        const body = s[id];
        const held = drag.current?.id === id;
        const idle = id === 'wine' ? 0 : Math.sin(s.time * 0.65 + (id === 'fern' ? 0 : 2)) * 9;
        const target = held ? body.target : idle + body.hover;
        const acceleration = (target - body.value) * (held ? 100 : 28) - body.velocity * (held ? 17 : 7);
        body.velocity += acceleration * dt;
        body.value += body.velocity * dt;
        body.hover *= Math.exp(-3 * dt);
      }
      if (drag.current?.id !== 'coin') {
        s.coin.velocity += (14 - s.coin.velocity) * (1 - Math.exp(-1.3 * dt));
        s.coin.value = (s.coin.value + s.coin.velocity * dt) % 360;
      }
      s.coin.hover *= Math.exp(-3 * dt);
      const liquidAcceleration = (s.wine.value - s.liquid) * 22 - s.liquidVelocity * 3.7;
      s.liquidVelocity += liquidAcceleration * dt;
      s.liquid = clamp(s.liquid + s.liquidVelocity * dt, -26, 26);
      s.ripple = clamp(s.ripple * Math.exp(-2 * dt) + Math.abs(s.wine.velocity) * dt * 0.018, 0, 1.1);
      draw();
      frame = window.requestAnimationFrame(tick);
    };
    const stop = () => {
      window.cancelAnimationFrame(frame);
      frame = 0;
      last = 0;
      release();
      ids.forEach(id => { state.current[id].velocity = 0; });
      state.current.liquidVelocity = 0;
    };
    const visibility = () => {
      stop();
      if (!document.hidden && ambient && !isExiting) frame = window.requestAnimationFrame(tick);
    };
    if (reducedMotion) {
      ids.forEach(id => { state.current[id].value = 0; state.current[id].hover = 0; });
      state.current.liquid = 0;
      state.current.ripple = 0;
    }
    draw(true);
    visibility();
    document.addEventListener('visibilitychange', visibility);
    window.addEventListener('blur', release);
    return () => {
      stop();
      drawRef.current = () => {};
      document.removeEventListener('visibilitychange', visibility);
      window.removeEventListener('blur', release);
    };
  }, [isExiting, paused, reducedMotion, liquidMask, release]);

  const bind = (id: ArtworkId) => ({
    onPointerDown: (event: ReactPointerEvent<HTMLButtonElement>) => {
      if (isExiting || event.button !== 0 || drag.current) return;
      const element = event.currentTarget;
      suppressClick.current = false;
      const scene = sceneRef.current?.querySelector<HTMLElement>('.landing-still-life');
      const scale = scene ? scene.getBoundingClientRect().width / scene.offsetWidth : 1;
      drag.current = {
        id, element, pointerId: event.pointerId, startX: event.clientX,
        startValue: state.current[id].value, lastX: event.clientX, lastTime: event.timeStamp, scale,
      };
      state.current[id].target = state.current[id].value;
      state.current[id].velocity = 0;
      element.setPointerCapture(event.pointerId);
      element.setAttribute('data-dragging', 'true');
    },
    onPointerMove: (event: ReactPointerEvent<HTMLButtonElement>) => {
      if (isExiting) return;
      const current = drag.current;
      const body = state.current[id];
      if (!current) {
        if (!paused && !reducedMotion && event.pointerType !== 'touch') {
          const rect = event.currentTarget.getBoundingClientRect();
          const proximity = clamp((event.clientX - rect.left) / rect.width - 0.5, -0.5, 0.5);
          body.hover = proximity * (id === 'wine' ? 3 : 30);
        }
        return;
      }
      if (current.id !== id || current.pointerId !== event.pointerId) return;
      const delta = (event.clientX - current.startX) / current.scale;
      if (Math.abs(delta) > 4) suppressClick.current = true;
      const manualOnly = paused || reducedMotion;
      if (id === 'coin') {
        body.value = current.startValue + delta * (reducedMotion ? 0.3 : 0.85);
        const dt = Math.max(8, event.timeStamp - current.lastTime) / 1000;
        body.velocity = clamp((event.clientX - current.lastX) / current.scale / dt * 0.85, -720, 720);
      } else {
        const limit = id === 'wine' ? (reducedMotion ? 6 : 18) : (reducedMotion ? 12 : 65);
        body.target = clamp(current.startValue + delta * (id === 'wine' ? 0.13 : 0.65), -limit, limit);
        if (manualOnly) body.value = body.target;
      }
      current.lastX = event.clientX;
      current.lastTime = event.timeStamp;
      if (manualOnly) state.current.liquid = state.current.wine.value;
      drawRef.current();
    },
    onPointerUp: (event: ReactPointerEvent<HTMLButtonElement>) => {
      if (drag.current?.pointerId !== event.pointerId) return;
      // Holding still before releasing should not replay an old flick.
      if (event.timeStamp - drag.current.lastTime > 100) state.current[id].velocity = 0;
      release();
    },
    onPointerCancel: (event: ReactPointerEvent<HTMLButtonElement>) => {
      if (drag.current?.pointerId === event.pointerId) {
        state.current[id].velocity = 0;
        release();
      }
    },
    onLostPointerCapture: () => release(),
    onKeyDown: (event: KeyboardEvent<HTMLButtonElement>) => {
      if (isExiting) return;
      if (event.key === 'Escape') {
        release();
        Object.assign(state.current[id], freshBody());
        if (id === 'wine') { state.current.liquid = 0; state.current.liquidVelocity = 0; }
        drawRef.current();
        return;
      }
      if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) return;
      event.preventDefault();
      const direction = event.key === 'ArrowLeft' || event.key === 'ArrowDown' ? -1 : 1;
      const body = state.current[id];
      if (id === 'coin') {
        body.value += direction * (reducedMotion ? 15 : 30);
        body.velocity = direction * 160;
      } else {
        const limit = id === 'wine' ? (reducedMotion ? 6 : 18) : (reducedMotion ? 12 : 65);
        body.value = clamp(body.value + direction * (id === 'wine' ? 4 : 12), -limit, limit);
      }
      if (paused || reducedMotion) state.current.liquid = state.current.wine.value;
      drawRef.current();
    },
    onClick: (event: ReactMouseEvent<HTMLButtonElement>) => {
      // Native button activation also works with Enter, Space, and assistive technology.
      if (suppressClick.current && event.detail > 0) { suppressClick.current = false; return; }
      suppressClick.current = false;
      if (isExiting) return;
      const body = state.current[id];
      if (id === 'coin') {
        body.velocity = 220;
        if (paused || reducedMotion) body.value += 20;
      } else {
        body.value = id === 'wine' ? 5 : 12;
      }
      if (paused || reducedMotion) state.current.liquid = state.current.wine.value;
      drawRef.current();
    },
  });

  return { sceneRef, paused, setPaused, reducedMotion, bind };
}
