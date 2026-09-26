import React, { useState, useEffect, useCallback, useRef } from 'react';
import './LandingPage.css';
import './LandingEditorial.css';
import { Link } from 'react-router-dom';
import { ArrowUpRight, ArrowRight } from 'lucide-react';
import { sound } from '../audio/soundEngine';
import { LandingBackdrop } from './LandingBackdrop';
import { publicAudio } from '../audio/publicAudio';
import './LandingEntrance.css';

interface LandingPageProps {
  onEnterCLI: () => void;
  onEnterDocs: () => void;
  onEnterAnalytics: () => void;
  isTurning?: boolean;
  isExiting?: boolean;
}

// Each entry is a complete letter, so typing never reveals partial ASCII rows.
const BITKAUN_LETTERS = [
  ['██████╗ ', '██╔══██╗', '██████╔╝', '██╔══██╗', '██████╔╝', '╚═════╝ '],
  ['██╗', '██║', '██║', '██║', '██║', '╚═╝'],
  ['████████╗', '╚══██╔══╝', '   ██║   ', '   ██║   ', '   ██║   ', '   ╚═╝   '],
  ['██╗  ██╗', '██║ ██╔╝', '█████╔╝ ', '██╔═██╗ ', '██║  ██╗', '╚═╝  ╚═╝'],
  [' █████╗ ', '██╔══██╗', '███████║', '██╔══██║', '██║  ██║', '╚═╝  ╚═╝'],
  ['██╗   ██╗', '██║   ██║', '██║   ██║', '██║   ██║', '╚██████╔╝', ' ╚═════╝ '],
  ['███╗   ██╗', '████╗  ██║', '██╔██╗ ██║', '██║╚██╗██║', '██║ ╚████║', '╚═╝  ╚═══╝'],
  ['██████╗ ', '╚════██╗', '  ▄███╔╝', '  ▀▀══╝ ', '  ██╗   ', '  ╚═╝   '],
].map(rows => rows.join('\n'));

export const LandingPage: React.FC<LandingPageProps> = ({ onEnterCLI, onEnterDocs, onEnterAnalytics, isExiting = false, isTurning = false }) => {
  const [intro, setIntro] = useState<'gate' | 'running' | 'ready'>(() => {
    try { return sessionStorage.getItem('bitkaun-opening-seen') === '1' ? 'ready' : 'gate'; } catch { return 'gate'; }
  });
  const [revealing, setRevealing] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const enterButton = useRef<HTMLButtonElement>(null);
  const skipButton = useRef<HTMLButtonElement>(null);
  const introActive = intro !== 'ready';
  const reveal = useCallback(() => setRevealing(true), []);
  const finishIntro = useCallback(() => {
    try { sessionStorage.setItem('bitkaun-opening-seen', '1'); } catch { /* Still usable without storage. */ }
    setIntro('ready');
    requestAnimationFrame(() => document.getElementById('landing-title')?.focus({ preventScroll: true }));
  }, []);
  const startIntro = () => {
    publicAudio.unlock();
    root.current?.scrollTo({ top: 0, behavior: 'instant' });
    setRevealing(false);
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) finishIntro();
    else setIntro('running');
  };
  const openDocs = (event: React.MouseEvent<HTMLAnchorElement>) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    onEnterDocs();
  };

  useEffect(() => { if (!introActive) return; return publicAudio.hold('landing-opening'); }, [introActive]);
  useEffect(() => {
    root.current?.querySelectorAll<HTMLElement>('.landing-masthead, .landing-hero-copy, .landing-index, .landing-colophon').forEach(element => { element.inert = introActive; });
    if (intro === 'gate') enterButton.current?.focus({ preventScroll: true });
    if (intro === 'running') skipButton.current?.focus({ preventScroll: true });
    const key = (event: KeyboardEvent) => { if (introActive && event.key === 'Escape') { event.preventDefault(); finishIntro(); } };
    window.addEventListener('keydown', key);
    return () => window.removeEventListener('keydown', key);
  }, [intro, introActive, finishIntro]);

  return (
    <div ref={root} className={`editorial landing-canvas intro-${intro}${revealing ? ' landing-revealing' : ''}${isExiting ? ' landing-canvas-exiting' : ''}`} aria-hidden={isExiting || undefined}>
      {introActive && <div className="landing-intro-wash" aria-hidden="true" />}
      {introActive && <div className={`landing-entry-gate${intro === 'running' ? ' landing-entry-departing' : ''}`} aria-hidden={intro === 'running' || undefined}>
        <span className="eyebrow">The art of following the evidence.</span>
        <div className="landing-entry-wordmark" role="img" aria-label="BITKAUN">{BITKAUN_LETTERS.map((letter, index) => <pre key={index} aria-hidden="true">{letter}</pre>)}</div>
        <p>A considered workspace.<br /><em>An investigative mindset.</em></p>
        <button ref={enterButton} className="editorial-button" onClick={startIntro} tabIndex={intro === 'running' ? -1 : 0}>Enter BitKaun <ArrowRight size={17} /></button>
        <span className="landing-entry-note">A little ceremony, before the investigation.</span>
      </div>}
      {intro === 'running' && <div className="landing-intro-controls"><span role="status">Setting the scene</span><button ref={skipButton} onClick={finishIntro}>Skip opening ↗</button></div>}
      <a className="skip-link" href="#landing-main">Skip to content</a>
      <header className="landing-masthead">
        <Link className="brand" to="/" aria-label="BitKaun home">BitKaun<span>?</span></Link>
        <span className="eyebrow masthead-note">The art of following the evidence.</span>
        <nav aria-label="Main navigation">
          <Link to="/docs/introduction" onClick={openDocs}>Field Guide</Link>
          <button disabled={isExiting} onClick={onEnterCLI}>Open Terminal <ArrowUpRight size={15} /></button>
        </nav>
      </header>
      <main className="landing-main" id="landing-main" tabIndex={-1}>
        <section className="landing-hero" aria-labelledby="landing-title">
          <div className="landing-hero-copy">
            <p className="eyebrow landing-kicker"><span /> Bitcoin forensics, thoughtfully explored.</p>
            <div className="landing-ascii-container" role="img" aria-label="BITKAUN">
            <div className="landing-ascii" aria-hidden="true">
              {BITKAUN_LETTERS.map((letter, index) => (
                <pre className="landing-ascii-letter" key={index} style={{ '--exit-delay': `${index * 35}ms`, '--letter-delay': `${index * 80}ms` } as React.CSSProperties}>{letter}</pre>
              ))}
               <span className="blink-cursor" />
            </div>
          </div>
            <h1 id="landing-title" tabIndex={-1}>Follow the flow.<br /><em>Understand</em><br />the evidence.</h1>
            <p className="landing-deck">A considered workspace for Bitcoin investigations. Trace transactions, explore connections, and uncover the story behind the data.</p>
            <div className="landing-actions">
              <button className="editorial-button" type="button" disabled={isExiting} onClick={() => { sound.playKeyClick(); onEnterCLI(); }}>Open Terminal <ArrowUpRight size={18} /></button>
              <Link className="editorial-text-link" to="/docs/introduction" onClick={openDocs}>Read the field guide <ArrowRight size={16} /></Link>
            </div>
            <p className="landing-footnote"><span className="landing-tiny-prompt">&gt;_</span> A local workspace. An investigative mindset.</p>
          </div>
          <div className="landing-gallery" aria-label="Interactive ASCII still life">
            <span className="gallery-edition eyebrow">A study in character / No. 01</span>
            <LandingBackdrop isExiting={isExiting || isTurning} introActive={introActive} introRunning={intro === 'running'} onReveal={reveal} onIntroComplete={finishIntro} />
            <div className="gallery-caption"><span className="eyebrow">Botanical proof</span><p>Organic forms. Digital instincts.</p></div>
          </div>
        </section>
        <nav className="landing-index" aria-label="Explore BitKaun">
          <button disabled={isExiting} onClick={onEnterCLI}><span className="eyebrow">01 / The workspace</span><span className="index-title">Investigate <ArrowUpRight size={20} /></span><span className="index-description">Follow transactions. Examine the evidence.</span></button>
          <Link to="/docs/introduction" onClick={openDocs}><span className="eyebrow">02 / The field guide</span><span className="index-title">Documentation <ArrowUpRight size={20} /></span><span className="index-description">Find your bearings, from setup to first case.</span></Link>
          <Link to="/analytics" onClick={event => { if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return; event.preventDefault(); onEnterAnalytics(); }}><span className="eyebrow">03 / The observatory</span><span className="index-title">Analytics <ArrowUpRight size={20} /></span><span className="index-description">Read the data. Understand the intelligence.</span></Link>
        </nav>
      </main>
      <footer className="landing-colophon"><span>BITKAUN? <span className="colophon-divider">/</span> Bitcoin intelligence, with perspective.</span><button className="landing-replay" onClick={startIntro}>Replay opening ↗</button><span>SIH PS146 <span className="colophon-divider">·</span> Local-first by design</span></footer>
    </div>
  );
};

export default LandingPage;
