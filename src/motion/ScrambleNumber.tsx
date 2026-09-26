import { useEffect, useState } from 'react';
import { useReveal } from './useReveal';

export function ScrambleNumber({ value }: { value: string }) {
  const reveal = useReveal<HTMLSpanElement>(value, 650);
  const [display, setDisplay] = useState(value);
  useEffect(() => {
    if (reveal.phase !== 'playing' || reveal.reduced) { setDisplay(value); return; }
    let frame = 0, last = -100;
    const started = performance.now();
    const digits = [...value].filter(char => /\d/.test(char)).length;
    const tick = (now: number) => {
      const elapsed = now - started;
      if (elapsed >= 620) { setDisplay(value); return; }
      if (elapsed - last >= 45) {
        last = elapsed; let digit = 0;
        setDisplay([...value].map(char => !/\d/.test(char) ? char : ++digit / digits < elapsed / 620 ? char : String(Math.floor(Math.random() * 10))).join(''));
      }
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, reveal.phase, reveal.reduced]);
  return <span ref={reveal.ref} className="scramble-number" data-reveal={reveal.phase}><span className="sr-only">{value}</span><span aria-hidden="true">{reveal.phase === 'playing' ? display : value}</span></span>;
}
