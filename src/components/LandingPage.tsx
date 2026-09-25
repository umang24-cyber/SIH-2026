import React, { useState, useEffect } from 'react';
import './LandingPage.css';
import { sound } from '../audio/soundEngine';
import { LandingBackdrop } from './LandingBackdrop';

interface LandingPageProps {
  onEnterCLI: () => void;
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

export const LandingPage: React.FC<LandingPageProps> = ({ onEnterCLI, isExiting = false }) => {
  const [visibleLetters, setVisibleLetters] = useState(0);
  const [showContent, setShowContent] = useState<boolean>(false);

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setVisibleLetters(BITKAUN_LETTERS.length);
      setShowContent(true);
      return;
    }

    let frame = 0;
    let revealTimer = 0;
    const start = performance.now();
    const type = (now: number) => {
      const length = Math.min(BITKAUN_LETTERS.length, Math.floor((now - start) / 3000 * BITKAUN_LETTERS.length));
      setVisibleLetters(length);
      if (length === BITKAUN_LETTERS.length) {
        revealTimer = window.setTimeout(() => setShowContent(true), 300);
      } else {
        frame = window.requestAnimationFrame(type);
      }
    };
    frame = window.requestAnimationFrame(type);

    return () => {
      window.cancelAnimationFrame(frame);
      window.clearTimeout(revealTimer);
    };
  }, []);

  return (
    <div className={`landing-canvas${isExiting ? ' landing-canvas-exiting' : ''}`} aria-hidden={isExiting || undefined}>
      <LandingBackdrop />

      <div className="landing-content">
        <div className="landing-header">
          <div className="landing-ascii-container" role="img" aria-label="BITKAUN forensic terminal">
            <div className="landing-ascii" aria-hidden="true">
              {BITKAUN_LETTERS.slice(0, visibleLetters).map((letter, index) => (
                <pre className="landing-ascii-letter" key={index} style={{ '--exit-delay': `${index * 35}ms` } as React.CSSProperties}>{letter}</pre>
              ))}
              <span className="blink-cursor" />
            </div>
          </div>
          <div className={`landing-subtitle ${showContent ? 'visible' : ''}`}>
            <span className="landing-tag">[ BITKAUN? FORENSIC TERMINAL ]</span>
            <span className="landing-version">v8.0.0 · SIH PS146</span>
          </div>
        </div>

        <div className={`landing-description ${showContent ? 'visible' : ''}`}>
          <p>
            AI-Powered Monitoring &amp; Analysis of Bitcoin Transaction Traffic.
            <br />
            Dual-layer forensic graph analytics for law enforcement and financial intelligence.
          </p>
        </div>

        <div className={`landing-cards ${showContent ? 'visible' : ''}`}>
          <button type="button" className="landing-card landing-card-action" disabled={!showContent || isExiting} onClick={() => { sound.playKeyClick(); onEnterCLI(); }}>
            <div className="card-border" />
            <div className="card-header">
              <span className="card-icon">[01]</span>
              <span className="card-title">CLI TOOL</span>
            </div>
            <div className="card-body">
              <p>Enter the forensic terminal and begin investigation.</p>
              <span className="card-hint">bitkaun@investigation:~#</span>
            </div>
          </button>

          <div className="landing-card landing-card-placeholder">
            <div className="card-border" />
            <div className="card-header">
              <span className="card-icon">[02]</span>
              <span className="card-title">DOCS</span>
            </div>
            <div className="card-body">
              <p>Learn the tool, commands, and architecture.</p>
              <span className="card-hint">MODULE NOT MOUNTED</span>
            </div>
          </div>

          <div className="landing-card landing-card-placeholder">
            <div className="card-border" />
            <div className="card-header">
              <span className="card-icon">[03]</span>
              <span className="card-title">ANALYTICS</span>
            </div>
            <div className="card-body">
              <p>Model performance, data ingested, and telemetry.</p>
              <span className="card-hint">DATA PENDING</span>
            </div>
          </div>
        </div>

        <div className={`landing-footer ${showContent ? 'visible' : ''}`}>
          <span className="landing-status-dot" />
          <span>SYSTEM ONLINE - AIR-GAPPED - OFFLINE</span>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
