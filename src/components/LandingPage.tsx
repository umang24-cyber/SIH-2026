import React, { useState, useEffect } from 'react';
import './LandingPage.css';
import './LandingEditorial.css';
import { Link } from 'react-router-dom';
import { ArrowUpRight, ArrowRight } from 'lucide-react';
import { sound } from '../audio/soundEngine';
import { LandingBackdrop } from './LandingBackdrop';

interface LandingPageProps {
  onEnterCLI: () => void;
  onEnterDocs: () => void;
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

export const LandingPage: React.FC<LandingPageProps> = ({ onEnterCLI, onEnterDocs, isExiting = false, isTurning = false }) => {
  const [visibleLetters, setVisibleLetters] = useState(0);
  const openDocs = (event: React.MouseEvent<HTMLAnchorElement>) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    onEnterDocs();
  };

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setVisibleLetters(BITKAUN_LETTERS.length);
      return;
    }

    let frame = 0;
    const start = performance.now();
    const type = (now: number) => {
      const length = Math.min(BITKAUN_LETTERS.length, Math.floor((now - start) / 1100 * BITKAUN_LETTERS.length));
      setVisibleLetters(length);
      if (length < BITKAUN_LETTERS.length) {
        frame = window.requestAnimationFrame(type);
      }
    };
    frame = window.requestAnimationFrame(type);

    return () => {
      window.cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <div className={`editorial landing-canvas${isExiting ? ' landing-canvas-exiting' : ''}`} aria-hidden={isExiting || undefined}>
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
              {BITKAUN_LETTERS.slice(0, visibleLetters).map((letter, index) => (
                <pre className="landing-ascii-letter" key={index} style={{ '--exit-delay': `${index * 35}ms` } as React.CSSProperties}>{letter}</pre>
              ))}
               <span className="blink-cursor" />
            </div>
          </div>
            <h1 id="landing-title">Follow the flow.<br /><em>Understand</em><br />the evidence.</h1>
            <p className="landing-deck">A considered workspace for Bitcoin investigations. Trace transactions, explore connections, and uncover the story behind the data.</p>
            <div className="landing-actions">
              <button className="editorial-button" type="button" disabled={isExiting} onClick={() => { sound.playKeyClick(); onEnterCLI(); }}>Open Terminal <ArrowUpRight size={18} /></button>
              <Link className="editorial-text-link" to="/docs/introduction" onClick={openDocs}>Read the field guide <ArrowRight size={16} /></Link>
            </div>
            <p className="landing-footnote"><span className="landing-tiny-prompt">&gt;_</span> A local workspace. An investigative mindset.</p>
          </div>
          <div className="landing-gallery" aria-label="Interactive ASCII still life">
            <span className="gallery-edition eyebrow">A study in character / No. 01</span>
            <LandingBackdrop isExiting={isExiting || isTurning} />
            <div className="gallery-caption"><span className="eyebrow">Botanical proof</span><p>Organic forms. Digital instincts.</p></div>
          </div>
        </section>
        <nav className="landing-index" aria-label="Explore BitKaun">
          <button disabled={isExiting} onClick={onEnterCLI}><span className="eyebrow">01 / The workspace</span><span className="index-title">Investigate <ArrowUpRight size={20} /></span><span className="index-description">Follow transactions. Examine the evidence.</span></button>
          <Link to="/docs/introduction" onClick={openDocs}><span className="eyebrow">02 / The field guide</span><span className="index-title">Documentation <ArrowUpRight size={20} /></span><span className="index-description">Find your bearings, from setup to first case.</span></Link>
          <div><span className="eyebrow">03 / The observatory</span><span className="index-title">Analytics <span className="coming-soon">Coming soon</span></span><span className="index-description">A future home for model and data insights.</span></div>
        </nav>
      </main>
      <footer className="landing-colophon"><span>BITKAUN? <span className="colophon-divider">/</span> Bitcoin intelligence, with perspective.</span><span>SIH PS146 <span className="colophon-divider">·</span> Local-first by design</span></footer>
    </div>
  );
};

export default LandingPage;
