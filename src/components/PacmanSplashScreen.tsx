import React, { useState, useEffect, useRef, useCallback } from 'react';
import { sound } from '../audio/soundEngine';
import './PacmanSplashScreen.css';

interface PacmanSplashScreenProps {
  onComplete: () => void;
  autoStart?: boolean;
  entranceFromLanding?: boolean;
  onEntranceComplete?: () => void;
}

interface BitcoinCoin {
  id: number;
  col: number;
  eaten: boolean;
}

const LOGO_LINES = [
  "██████╗ ██╗████████╗██╗  ██╗ █████╗ ██╗   ██╗███╗   ██╗██████╗ ",
  "██╔══██╗██║╚══██╔══╝██║ ██╔╝██╔══██╗██║   ██║████╗  ██║╚════██╗",
  "██████╔╝██║   ██║   █████╔╝ ███████║██║   ██║██╔██╗ ██║  ▄███╔╝",
  "██╔══██╗██║   ██║   ██╔═██╗ ██╔══██║██║   ██║██║╚██╗██║  ▀▀══╝ ",
  "██████╔╝██║   ██║   ██║  ██╗██║  ██║╚██████╔╝██║ ╚████║  ██╗   ",
  "╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝  ╚═╝   "
];

const TOTAL_COLS = 64;
const BITCOIN_COLS = [8, 17, 26, 35, 44, 53, 62];
const GLITCH_CHARS = ['#', '░', '▒', '▓', '%', '&', '*', '@', '?', '0', '1', '!', '/', 'X', 'Z', '█'];

export const PacmanSplashScreen: React.FC<PacmanSplashScreenProps> = ({
  onComplete, autoStart = false, entranceFromLanding = false, onEntranceComplete,
}) => {
  const [isEntering, setIsEntering] = useState(() =>
    entranceFromLanding && !window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );
  const [hasStarted, setHasStarted] = useState<boolean>(false);
  const [currentCol, setCurrentCol] = useState<number>(0);
  const [mouthOpen, setMouthOpen] = useState<boolean>(true);
  const [isFinished, setIsFinished] = useState<boolean>(false);
  const [bitcoins, setBitcoins] = useState<BitcoinCoin[]>(
    BITCOIN_COLS.map((col, i) => ({ id: i + 1, col, eaten: false }))
  );

  const timerRef = useRef<number | null>(null);
  const finishTimerRef = useRef<number | null>(null);
  const startedRef = useRef(false);
  const completedRef = useRef(false);
  const chompCounterRef = useRef<number>(0);
  const audioStopRef = useRef<(() => void) | null>(null);
  const entranceCompletedRef = useRef(false);
  const splashRef = useRef<HTMLDivElement>(null);

  const startSequence = useCallback(() => {
    if (startedRef.current || completedRef.current || isEntering) return;
    startedRef.current = true;
    setHasStarted(true);
    sound.initCtx();
  }, [isEntering]);

  const finishEntrance = useCallback(() => {
    if (entranceCompletedRef.current || completedRef.current) return;
    entranceCompletedRef.current = true;
    setIsEntering(false);
    onEntranceComplete?.();
  }, [onEntranceComplete]);

  const handleSkip = useCallback(() => {
    if (completedRef.current) return;
    completedRef.current = true;
    if (timerRef.current !== null) clearInterval(timerRef.current);
    if (finishTimerRef.current !== null) clearTimeout(finishTimerRef.current);
    audioStopRef.current?.();
    sound.stopPacmanIntro();
    onComplete();
  }, [onComplete]);

  useEffect(() => {
    splashRef.current?.focus({ preventScroll: true });
  }, []);

  useEffect(() => {
    if (!entranceFromLanding) return;
    if (!isEntering) {
      finishEntrance();
      return;
    }

    // Animation-end is the handoff; the timer also handles paused/disabled CSS.
    const fallback = window.setTimeout(finishEntrance, 2300);
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onMotionChange = () => { if (motion.matches) finishEntrance(); };
    motion.addEventListener('change', onMotionChange);
    return () => {
      window.clearTimeout(fallback);
      motion.removeEventListener('change', onMotionChange);
    };
  }, [entranceFromLanding, isEntering, finishEntrance]);

  useEffect(() => {
    if (autoStart && !isEntering) startSequence();
  }, [autoStart, isEntering, startSequence]);

  useEffect(() => {
    if (!hasStarted) return;
    const stopAudio = sound.playPacmanIntro();
    audioStopRef.current = stopAudio;
    return () => {
      stopAudio();
      audioStopRef.current = null;
    };
  }, [hasStarted]);

  useEffect(() => {
    if (!isEntering) return;
    const chomp = window.setInterval(() => setMouthOpen(open => !open), 130);
    return () => window.clearInterval(chomp);
  }, [isEntering]);

  useEffect(() => () => {
    if (timerRef.current !== null) clearInterval(timerRef.current);
    if (finishTimerRef.current !== null) clearTimeout(finishTimerRef.current);
  }, []);

  // Keyboard controls
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' || (hasStarted && e.key === ' ')) {
        e.preventDefault();
        handleSkip();
      } else if (!isEntering && !hasStarted && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault();
        startSequence();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [hasStarted, isEntering, handleSkip, startSequence]);

  // Frame-by-frame column reveal & discrete Pac-Man walk
  useEffect(() => {
    if (!hasStarted) return;

    let col = 0;
    const stepInterval = 55; // 55ms per column (~3.5s total duration)

    timerRef.current = window.setInterval(() => {
      col++;
      setCurrentCol(col);
      setMouthOpen(col % 2 === 0);

      // Check if Pac-Man eats any Bitcoin at this column
      setBitcoins(prev =>
        prev.map(btc => {
          if (!btc.eaten && col >= btc.col - 1) {
            chompCounterRef.current++;
            sound.playPacmanChomp(chompCounterRef.current);
            return { ...btc, eaten: true };
          }
          return btc;
        })
      );

      // Finish when Pac-Man reaches the end of the 64 columns
      if (col >= TOTAL_COLS) {
        if (timerRef.current) clearInterval(timerRef.current);
        setIsFinished(true);
        setBitcoins(prev => prev.map(b => ({ ...b, eaten: true })));

        finishTimerRef.current = window.setTimeout(handleSkip, 500);
      }
    }, stepInterval);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [hasStarted, handleSkip]);

  // Generate the scrambled/revealed ASCII logo string for the current frame
  const getScrambledLogo = (): string => {
    if (isFinished) {
      return LOGO_LINES.join('\n');
    }

    return LOGO_LINES.map(line => {
      let out = '';
      for (let c = 0; c < line.length; c++) {
        const char = line[c];
        if (c <= currentCol - 2) {
          // Fully decoded and revealed target character
          out += char;
        } else if (c <= currentCol) {
          // Glitching scrambler frontier character
          if (char === ' ') {
            out += ' ';
          } else {
            out += GLITCH_CHARS[Math.floor(Math.random() * GLITCH_CHARS.length)];
          }
        } else {
          // Ahead of Pac-Man: not yet revealed
          out += ' ';
        }
      }
      return out;
    }).join('\n');
  };

  const pacmanPercent = Math.min(100, Math.max(0, (currentCol / TOTAL_COLS) * 100));

  return (
    <div
      ref={splashRef}
      className={`pacman-splash${isEntering ? ' pacman-splash-entering' : ''}`}
      role="dialog"
      aria-modal="true"
      aria-label="Starting BITKAUN terminal"
      tabIndex={-1}
      onClick={!hasStarted && !isEntering ? startSequence : undefined}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100dvh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 99999,
        cursor: !hasStarted && !isEntering ? 'pointer' : 'default',
        userSelect: 'none',
        overflow: 'hidden'
      }}
    >
      {/* Central Stage: Pac-Man Corridor & Revealing ASCII Art Logo */}
      <div
        style={{
          width: '90%',
          maxWidth: '780px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          position: 'relative'
        }}
      >
        {/* Track with Pacman Eating Green Bitcoins */}
        <div
          style={{
            width: '100%',
            height: '70px',
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            marginBottom: '16px'
          }}
        >
          {/* Green Pixel Bitcoins Line */}
          {bitcoins.map(btc => {
            const btcPercent = (btc.col / TOTAL_COLS) * 100;
            return (
              <div
                key={btc.id}
                className="pacman-splash-coin"
                style={{
                  position: 'absolute',
                  left: `${btcPercent}%`,
                  top: '50%',
                  transform: 'translate(-50%, -50%)',
                  opacity: btc.eaten ? 0 : 1,
                  transition: 'none',
                  zIndex: 2
                }}
              >
                <svg width="30" height="30" viewBox="0 0 16 16" shapeRendering="crispEdges">
                  <path
                    d="M5 1h6v1h2v2h1v2h1v4h-1v2h-1v2h-2v1H5v-1H3v-2H2v-2H1V7h1V5h1V3h2V1z"
                    fill="#00cc55"
                  />
                  <path
                    d="M6 3h1v1h1v-1h1v1h2v1h1v2h-1v1h1v2h-1v1H9v1H8v-1H7v1H6v-1H5V3h1zm1 2v2h2v-2H7zm0 3v2h2v-2H7z"
                    fill="#000000"
                  />
                </svg>
              </div>
            );
          })}

          {/* Green Pixel Pac-Man Sprite (Moving Clunkily Step-by-Step) */}
          <div
            className="pacman-splash-position"
            style={{
              position: 'absolute',
              left: `${pacmanPercent}%`,
              top: '50%',
              transform: 'translate(-50%, -50%)',
              zIndex: 10,
              transition: 'none'
            }}
          >
            <div
              className="pacman-splash-sprite"
              onAnimationEnd={event => {
                if (event.target === event.currentTarget && event.animationName === 'pacman-enter-frame') finishEntrance();
              }}
            >
            {mouthOpen ? (
              <svg width="44" height="44" viewBox="0 0 16 16" shapeRendering="crispEdges">
                <path
                  d="M5 1h6v1h2v2h1v2h-5v1H7v2h2v1h6v2h-1v2h-2v1H5v-1H3v-2H2v-2H1V7h1V5h1V3h2V1z"
                  fill="#00cc55"
                />
                <rect x="8" y="3" width="2" height="2" fill="#000000" />
              </svg>
            ) : (
              <svg width="44" height="44" viewBox="0 0 16 16" shapeRendering="crispEdges">
                <path
                  d="M5 1h6v1h2v2h1v2h1v4h-1v2h-1v2h-2v1H5v-1H3v-2H2v-2H1V7h1V5h1V3h2V1z"
                  fill="#00cc55"
                />
                <rect x="8" y="3" width="2" height="2" fill="#000000" />
                <rect x="11" y="8" width="4" height="1" fill="#000000" />
              </svg>
            )}
            </div>
          </div>
        </div>

        {/* The Frame-by-Frame Revealed Scrambled ASCII Art Logo */}
        <pre
          className="ansi-shadow-logo pacman-splash-logo"
          style={{
            color: 'var(--fg-primary)',
            fontSize: 'clamp(7px, 1.85vw, 14.5px)',
            lineHeight: 1.15,
            letterSpacing: '0px',
            whiteSpace: 'pre',
            margin: 0,
            textShadow: isFinished ? '0 0 4px rgba(0, 204, 85, 0.5)' : '0 0 2px rgba(0, 204, 85, 0.3)'
          }}
        >
          {hasStarted ? getScrambledLogo() : LOGO_LINES.map(line => ' '.repeat(line.length)).join('\n')}
        </pre>
      </div>

      {/* Startup Prompt on Blank Black Screen */}
      {!hasStarted && !autoStart && !isEntering ? (
        <div
          style={{
            position: 'absolute',
            bottom: '20%',
            color: '#00cc55',
            fontFamily: "'VT323', monospace",
            fontSize: '22px',
            letterSpacing: '2px',
            animation: 'cursor-blink 0.8s step-start infinite',
            textAlign: 'center'
          }}
        >
          [ CLICK TO BOOTUP BITKAUN ]
        </div>
      ) : (
        <button
          type="button"
          className="pacman-splash-skip"
          onClick={handleSkip}
          style={{
            position: 'absolute',
            bottom: '24px',
            color: '#005520',
            fontFamily: "'VT323', monospace",
            fontSize: '15px',
            cursor: 'pointer',
            letterSpacing: '1px',
            background: 'none',
            border: 0,
            padding: '8px 12px'
          }}
        >
          [ESC to skip]
        </button>
      )}
    </div>
  );
};
