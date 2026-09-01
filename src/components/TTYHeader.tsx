import React, { useState, useEffect } from 'react';
import { ViewMode } from '../types/terminal';
import { sound } from '../audio/soundEngine';

interface TTYHeaderProps {
  activeView: ViewMode;
  targetId?: string | null;
  nodeCount: number;
  linkCount: number;
}

export const TTYHeader: React.FC<TTYHeaderProps> = ({
  activeView,
  targetId,
  nodeCount,
  linkCount
}) => {
  const [timeStr, setTimeStr] = useState<string>('');
  const [audioState, setAudioState] = useState<boolean>(sound.isEnabled());

  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setTimeStr(d.toTimeString().split(' ')[0] + ' UTC');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const checkAudio = () => setAudioState(sound.isEnabled());
    const interval = setInterval(checkAudio, 500);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="tty-status-bar" role="banner">
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <span className="tty-tag">BITKAUN-OS:ACTIVE</span>
        <span style={{ color: '#33ff88' }}>
          [root@bitkaun-forensics-terminal]:/sys/kernel/debug/bitkaun-matrix#
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap', fontSize: '14px' }}>
        <span>
          VIEW: <span className="tty-tag-dim" style={{ color: '#00ff66', fontWeight: 'bold' }}>[{activeView}]</span>
        </span>
        {targetId && (
          <span>
            TARGET: <span style={{ color: '#33ff88' }}>{targetId}</span>
          </span>
        )}
        <span>
          GRAPH: <span style={{ color: '#00ff66' }}>{nodeCount}N / {linkCount}E</span>
        </span>
        <span>
          SOUND: <span style={{ color: audioState ? '#00ff66' : '#888888' }}>{audioState ? 'SYNTH_ON' : 'MUTED'}</span>
        </span>
        <span style={{ color: '#00ff66' }}>{timeStr}</span>
      </div>
    </header>
  );
};
