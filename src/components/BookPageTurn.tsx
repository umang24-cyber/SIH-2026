import { useEffect, useRef, type ReactNode } from 'react';
import './BookPageTurn.css';
import { publicAudio } from '../audio/publicAudio';

/** Keep the actual landing DOM on the cover, including its current scroll position. */
export function BookPageTurn({ turning, onComplete, children }: { turning: boolean; onComplete: () => void; children: ReactNode }) {
  const front = useRef<HTMLDivElement>(null);
  const skip = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (front.current) front.current.inert = turning;
    if (!turning) return;
    const stopSound = publicAudio.sequence('book-turn', [{ at: 70, type: 'book' }], 1500);
    skip.current?.focus({ preventScroll: true });
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onPreference = () => { if (preference.matches) onComplete(); };
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') { event.preventDefault(); onComplete(); } };
    const onHidden = () => { if (document.hidden) onComplete(); };
    const fallback = window.setTimeout(onComplete, 1650);
    preference.addEventListener('change', onPreference);
    window.addEventListener('keydown', onKey);
    document.addEventListener('visibilitychange', onHidden);
    onPreference();
    return () => { stopSound(); clearTimeout(fallback); preference.removeEventListener('change', onPreference); window.removeEventListener('keydown', onKey); document.removeEventListener('visibilitychange', onHidden); };
  }, [turning, onComplete]);

  return <div className={`book-stage${turning ? ' book-turning' : ''}`}>
    {turning && <><div className="book-reveal-shade" aria-hidden="true" /><div className="book-follow-leaf" aria-hidden="true" /></>}
    <div className="book-cover" onAnimationEnd={event => { if (turning && event.target === event.currentTarget && event.animationName === 'book-cover-turn') onComplete(); }}>
      <div className="book-cover-front" ref={front} aria-hidden={turning || undefined}>{children}<span className="book-cover-light" aria-hidden="true" /></div>
      {turning && <div className="book-cover-back editorial" aria-hidden="true"><div className="book-endpaper"><span className="eyebrow">The BitKaun Field Guide</span><span className="book-endpaper-mark">B<span>?</span></span><span className="eyebrow">A little context. A clearer perspective.</span></div></div>}
    </div>
    {turning && <div className="book-turn-controls editorial"><span role="status">Opening the field guide</span><button ref={skip} onClick={onComplete}>Skip page turn <span aria-hidden="true">↗</span></button></div>}
  </div>;
}
