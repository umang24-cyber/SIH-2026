import React, { useState, useEffect, useRef } from 'react';
import { sound } from '../audio/soundEngine';

interface ScrambledAsciiLogoProps {
  active?: boolean;
  onComplete?: () => void;
}

const FINAL_LOGO = `██████╗ ██╗████████╗██╗  ██╗ █████╗ ██╗   ██╗███╗   ██╗██████╗ 
██╔══██╗██║╚══██╔══╝██║ ██╔╝██╔══██╗██║   ██║████╗  ██║╚════██╗
██████╔╝██║   ██║   █████╔╝ ███████║██║   ██║██╔██╗ ██║  ▄███╔╝
██╔══██╗██║   ██║   ██╔═██╗ ██╔══██║██║   ██║██║╚██╗██║  ▀▀══╝ 
██████╔╝██║   ██║   ██║  ██╗██║  ██║╚██████╔╝██║ ╚████║  ██╗   
╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝  ╚═╝   `;

const GLITCH_CHARS = ['#', '░', '▒', '▓', '%', '&', '*', '@', '?', '0', '1', '!', '/', '\\', 'X', 'Z', '█'];

export const ScrambledAsciiLogo: React.FC<ScrambledAsciiLogoProps> = ({ active = true, onComplete }) => {
  const [displayText, setDisplayText] = useState<string>('');
  const [isResolved, setIsResolved] = useState<boolean>(false);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    if (!active) return;

    let startTime: number | null = null;
    const duration = 1400; // 1.4 seconds scramble time
    const tickRef = { count: 0 };

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Play subtle tick sound every 3 frames
      tickRef.count++;
      if (tickRef.count % 3 === 0) {
        sound.playKeyClick();
      }

      // Generate scrambled text
      const chars = FINAL_LOGO.split('');
      const totalChars = chars.length;

      const scrambled = chars.map((char, index) => {
        if (char === ' ' || char === '\n' || char === '\r') {
          return char;
        }

        // Staggered threshold from left-to-right
        const charThreshold = (index / totalChars) * 0.85;

        if (progress > charThreshold) {
          return char;
        }

        const randomGlitch = GLITCH_CHARS[Math.floor(Math.random() * GLITCH_CHARS.length)];
        return randomGlitch;
      }).join('');

      setDisplayText(scrambled);

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate);
      } else {
        setDisplayText(FINAL_LOGO);
        setIsResolved(true);
        if (onComplete) onComplete();
      }
    };

    frameRef.current = requestAnimationFrame(animate);

    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, [active, onComplete]);

  return (
    <pre
      className="ansi-shadow-logo"
      style={{
        color: isResolved ? 'var(--fg-primary)' : 'var(--fg-highlight)',
        textShadow: isResolved ? 'none' : '0 0 4px rgba(0, 255, 102, 0.7)'
      }}
    >
      {displayText || FINAL_LOGO}
    </pre>
  );
};
