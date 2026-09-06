import React, { useState, useEffect } from 'react';

interface CliSpinnerProps {
  label?: string;
  className?: string;
  style?: React.CSSProperties;
}

const SPINNER_FRAMES = ['/', '-', '\\', '|'];

export const CliSpinner: React.FC<CliSpinnerProps> = ({
  label = 'PROCESSING...',
  className = '',
  style = {}
}) => {
  const [frameIndex, setFrameIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setFrameIndex(prev => (prev + 1) % SPINNER_FRAMES.length);
    }, 80);

    return () => clearInterval(interval);
  }, []);

  return (
    <span
      className={`cli-spinner ${className}`}
      style={{
        fontFamily: 'monospace',
        color: '#00ff66',
        letterSpacing: '1px',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '8px',
        ...style
      }}
    >
      <span style={{ color: '#33ff88', fontWeight: 'bold' }}>
        [{SPINNER_FRAMES[frameIndex]}]
      </span>
      {label && <span style={{ color: '#aaffaa' }}>{label}</span>}
    </span>
  );
};

export default CliSpinner;
