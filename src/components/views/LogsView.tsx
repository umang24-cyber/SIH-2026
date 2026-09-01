import React, { useState, useEffect, useRef } from 'react';
import { KernelLogEntry } from '../../types/terminal';

interface LogsViewProps {
  logs: KernelLogEntry[];
  onRunCommand: (cmd: string) => void;
}

export const LogsView: React.FC<LogsViewProps> = ({ logs, onRunCommand }) => {
  const [filterLevel, setFilterLevel] = useState<string>('ALL');
  const [isStreaming, setIsStreaming] = useState<boolean>(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isStreaming && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isStreaming]);

  const filteredLogs = filterLevel === 'ALL'
    ? logs
    : logs.filter(l => l.level === filterLevel);

  const getLevelStyle = (level: string) => {
    switch (level) {
      case 'CRIT':
        return { color: '#ff3344', fontWeight: 'bold' };
      case 'WARN':
        return { color: '#ffcc00', fontWeight: 'bold' };
      case 'IPC':
        return { color: '#33ff88' };
      case 'SYS':
        return { color: '#00ff66', opacity: 0.8 };
      default:
        return { color: '#00ff66' };
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', fontSize: '15px' }}>
      <div style={{ borderBottom: '1px solid #00ff66', paddingBottom: '6px', marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
        <h2 style={{ fontSize: '18px', color: '#33ff88' }}>
          &gt; KERNEL DMESG &amp; REALTIME INTERCEPT STREAM (/var/log/holmes-kernel.log)
        </h2>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ fontSize: '13px', color: '#007a33' }}>FILTER:</span>
          {['ALL', 'CRIT', 'WARN', 'INFO', 'IPC'].map(lvl => (
            <button
              key={lvl}
              onClick={() => setFilterLevel(lvl)}
              style={{
                background: filterLevel === lvl ? '#00ff66' : 'transparent',
                color: filterLevel === lvl ? '#000000' : '#00ff66',
                border: '1px solid #007a33',
                padding: '1px 6px',
                fontSize: '13px',
                cursor: 'pointer'
              }}
            >
              {lvl}
            </button>
          ))}
          <button
            onClick={() => setIsStreaming(!isStreaming)}
            style={{
              background: isStreaming ? '#003311' : '#330000',
              color: isStreaming ? '#33ff88' : '#ff4444',
              border: `1px solid ${isStreaming ? '#00ff66' : '#ff4444'}`,
              padding: '1px 8px',
              fontSize: '13px',
              cursor: 'pointer',
              marginLeft: '6px'
            }}
          >
            {isStreaming ? 'STREAM: ACTIVE' : 'STREAM: PAUSED'}
          </button>
        </div>
      </div>

      <div style={{ background: '#000502', border: '1px solid #004d20', padding: '8px', minHeight: '320px', maxHeight: '55vh', overflowY: 'auto', fontFamily: 'var(--font-code)' }}>
        {filteredLogs.map(entry => (
          <div key={entry.id} style={{ display: 'flex', gap: '10px', marginBottom: '4px', lineHeight: 1.35 }}>
            <span style={{ color: '#007a33', flexShrink: 0 }}>{entry.uptime}</span>
            <span style={{ color: '#00aa44', flexShrink: 0, width: '130px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              [{entry.source}]
            </span>
            <span style={{ ...getLevelStyle(entry.level), flexShrink: 0, width: '50px' }}>
              [{entry.level}]
            </span>
            <span style={{ color: '#00ff66', wordBreak: 'break-all' }}>
              {entry.message}
            </span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div style={{ marginTop: '10px', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', color: '#007a33', fontSize: '14px' }}>
        <span>Showing {filteredLogs.length} logged kernel entries</span>
        <span>
          Try: <span className="cmd-clickable" onClick={() => onRunCommand('inspect 0x77DD9900')}>inspect 0x77DD9900</span> | <span className="cmd-clickable" onClick={() => onRunCommand('graph')}>graph</span>
        </span>
      </div>
    </div>
  );
};
