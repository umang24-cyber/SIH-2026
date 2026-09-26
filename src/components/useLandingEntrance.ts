import { useLayoutEffect, useRef, type RefObject } from 'react';
import { publicAudio } from '../audio/publicAudio';

const clamp = (n: number) => Math.max(0, Math.min(1, n));
const ease = (n: number) => { const t = clamp(n); return t * t * (3 - 2 * t); };

export function useLandingEntrance(active: boolean, sceneRef: RefObject<HTMLDivElement>, setFrame: (fill: number, rotation: number, time: number) => void, onReveal: () => void, onComplete: () => void) {
  const bottleRef = useRef<HTMLPreElement>(null);
  const streamRef = useRef<SVGSVGElement>(null);
  useLayoutEffect(() => {
    if (!active || !sceneRef.current) return;
    const scene = sceneRef.current;
    const wine = scene.querySelector<HTMLElement>('.landing-art-wine')!;
    const coin = scene.querySelector<HTMLElement>('.landing-art-bitcoin')!;
    const ferns = [...scene.querySelectorAll<HTMLElement>('.landing-art-fern, .landing-art-fern-low')];
    const stillLife = scene.querySelector<HTMLElement>('.landing-still-life')!;
    const root = scene.closest<HTMLElement>('.landing-canvas')!;
    const wineRect = wine.getBoundingClientRect(), coinRect = coin.getBoundingClientRect();
    const scale = stillLife.getBoundingClientRect().width / stillLife.offsetWidth;
    const width = window.innerWidth, height = window.innerHeight;
    const glassHeight = Math.min(height * .48, width < 760 ? width * .9 : 490);
    const wineScale = glassHeight / wineRect.height;
    const coinScale = Math.min(205, width * .28) / coinRect.width;
    const wineCenter = { x: width * .43, y: height * .63 };
    const coinCenter = { x: width * .68, y: height * .65 };
    const rimY = wineCenter.y - glassHeight / 2 + glassHeight * .05;
    const liquidRowCount = scene.querySelectorAll('[data-liquid-row]').length;
    let frame = 0, finished = false, revealed = false;
    const started = performance.now();
    const stopSound = publicAudio.sequence('landing', [
      { at: 0, type: 'depart' }, { at: 600, type: 'pour', duration: 1850 },
      { at: 1120, type: 'flip' }, { at: 2700, type: 'glass' },
      { at: 3170, type: 'ding' }, { at: 4250, type: 'leaf' },
      { at: 4500, type: 'leaf' }, { at: 4950, type: 'reveal' },
    ], 5700);
    const reset = () => {
      [wine, coin, ...ferns].forEach(element => { element.style.removeProperty('transform'); element.style.removeProperty('opacity'); element.style.removeProperty('scale'); });
      root.removeAttribute('data-landing-phase');
      setFrame(1, 0, 0);
    };
    const finish = () => { if (finished) return; finished = true; cancelAnimationFrame(frame); stopSound(); reset(); onComplete(); };
    const tick = (now: number) => {
      if (finished) return;
      const t = now - started;
      const enter = ease(t / 550), pour = clamp((t - 620) / 1780);
      const flight = clamp((t - 1120) / 2050);
      const settle = ease((t - 3250) / 1150);
      const lift = Math.sin(Math.PI * flight) * height * .47;
      const place = (element: HTMLElement, rect: DOMRect, center: { x: number; y: number }, initialScale: number, angle: number) => {
        const dx = (center.x - rect.left - rect.width / 2) * (1 - settle) / scale;
        const dy = (center.y - rect.top - rect.height / 2) * (1 - settle) / scale;
        element.style.transform = `translate(${dx}px, ${dy}px) scale(${initialScale + (1 - initialScale) * settle}) rotate(${angle}deg)`;
      };
      place(wine, wineRect, wineCenter, wineScale, 0);
      place(coin, coinRect, { x: coinCenter.x, y: coinCenter.y - lift }, coinScale, 6 * settle);
      wine.style.opacity = String(enter); coin.style.opacity = String(ease((t - 700) / 350));
      setFrame(pour, flight * 1080, t / 1000);
      ferns.forEach((fern, index) => {
        const p = clamp((t - 4200 - index * 220) / 650);
        const spring = 1 - Math.pow(1 - p, 3) + Math.sin(p * Math.PI * 2) * .08 * (1 - p);
        fern.style.opacity = String(ease(p * 2)); fern.style.scale = String(.5 + spring * .5);
      });
      if (bottleRef.current) {
        const bottle = bottleRef.current;
        const arrive = ease((t - 200) / 450), depart = ease((t - 2630) / 500);
        bottle.style.transform = `translate(${wineCenter.x - bottle.offsetWidth / 2 - (1 - arrive) * 110 - depart * 140}px, ${rimY - 92 - depart * 100}px) rotate(${100 + arrive * 25 - depart * 35}deg)`;
        bottle.style.opacity = String(arrive * (1 - depart));
      }
      if (streamRef.current) {
        const flowing = ease((t - 610) / 130) * (1 - ease((t - 2350) / 170));
        const liquidY = wineCenter.y - glassHeight / 2 + (29 - 13 * pour) / liquidRowCount * glassHeight;
        streamRef.current.style.opacity = String(flowing);
        streamRef.current.querySelector('path')?.setAttribute('d', `M${wineCenter.x},${rimY - 84} Q${wineCenter.x + Math.sin(t / 160) * 3},${rimY - 32} ${wineCenter.x + Math.sin(t / 100) * 2},${liquidY}`);
        streamRef.current.querySelector('ellipse')?.setAttribute('cx', String(wineCenter.x));
        streamRef.current.querySelector('ellipse')?.setAttribute('cy', String(liquidY));
      }
      root.dataset.landingPhase = t < 600 ? 'arrive' : t < 2400 ? 'pour' : t < 3250 ? 'coin' : t < 4200 ? 'settle' : t < 4900 ? 'leaves' : 'brand';
      if (t >= 4850 && !revealed) { revealed = true; onReveal(); }
      if (t >= 5700) finish(); else frame = requestAnimationFrame(tick);
    };
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const reduced = () => { if (media.matches) finish(); };
    const hidden = () => { if (document.hidden) finish(); };
    const fallback = window.setTimeout(finish, 6500);
    window.addEventListener('resize', finish); document.addEventListener('visibilitychange', hidden); media.addEventListener('change', reduced);
    frame = requestAnimationFrame(tick);
    return () => { finished = true; cancelAnimationFrame(frame); clearTimeout(fallback); stopSound(); reset(); window.removeEventListener('resize', finish); document.removeEventListener('visibilitychange', hidden); media.removeEventListener('change', reduced); };
  }, [active, sceneRef, setFrame, onReveal, onComplete]);
  return { bottleRef, streamRef };
}
