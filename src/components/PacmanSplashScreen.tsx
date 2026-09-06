import React, { useState, useEffect, useRef } from 'react';
import { sound } from '../audio/soundEngine';

interface PacmanSplashScreenProps {
  onComplete: () => void;
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

export const PacmanSplashScreen: React.FC<PacmanSplashScreenProps> = ({ onComplete }) => {
  const [hasStarted, setHasStarted] = useState<boolean>(false);
  const [currentCol, setCurrentCol] = useState<number>(0);
  const [mouthOpen, setMouthOpen] = useState<boolean>(true);
  const [isFinished, setIsFinished] = useState<boolean>(false);
  const [bitcoins, setBitcoins] = useState<BitcoinCoin[]>(
    BITCOIN_COLS.map((col, i) => ({ id: i + 1, col, eaten: false }))
  );

  const timerRef = useRef<number | null>(null);
  const chompCounterRef = useRef<number>(0);
  const audioStopRef = useRef<(() => void) | null>(null);

  const startSequence = () => {
    if (hasStarted) return;
    setHasStarted(true);
    sound.initCtx();
    const stopAudio = sound.playPacmanIntro();
    audioStopRef.current = stopAudio;
  };

  // Keyboard controls
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!hasStarted) {
        startSequence();
      } else if (e.key === 'Escape' || e.key === ' ') {
        handleSkip();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [hasStarted]);

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

        setTimeout(() => {
          onComplete();
        }, 500);
      }
    }, stepInterval);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [hasStarted, onComplete]);

  const handleSkip = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (audioStopRef.current) {
      audioStopRef.current();
    }
    sound.stopPacmanIntro();
    onComplete();
  };

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
      onClick={!hasStarted ? startSequence : undefined}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        backgroundColor: '#000000',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 99999,
        cursor: !hasStarted ? 'pointer' : 'default',
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
            style={{
              position: 'absolute',
              left: `${pacmanPercent}%`,
              top: '50%',
              transform: 'translate(-50%, -50%)',
              zIndex: 10,
              transition: 'none'
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

        {/* The Frame-by-Frame Revealed Scrambled ASCII Art Logo */}
        <pre
          className="ansi-shadow-logo"
          style={{
            color: 'var(--fg-primary)',
            fontSize: '14.5px',
            lineHeight: 1.15,
            letterSpacing: '0px',
            whiteSpace: 'pre',
            margin: 0,
            textShadow: isFinished ? '0 0 4px rgba(0, 204, 85, 0.5)' : '0 0 2px rgba(0, 204, 85, 0.3)'
          }}
        >
          {getScrambledLogo()}
        </pre>
      </div>

      {/* Startup Prompt on Blank Black Screen */}
      {!hasStarted ? (
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
        <div
          onClick={handleSkip}
          style={{
            position: 'absolute',
            bottom: '24px',
            color: '#005520',
            fontFamily: "'VT323', monospace",
            fontSize: '15px',
            cursor: 'pointer',
            letterSpacing: '1px'
          }}
        >
          [ESC to skip]
        </div>
      )}
    </div>
  );
};
