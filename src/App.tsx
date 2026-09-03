import React, { useState, useEffect, useRef } from 'react';
import { sound } from './audio/soundEngine';
import { CliOutputRenderer } from './components/CliOutputRenderer';
import { PacmanSplashScreen } from './components/PacmanSplashScreen';
import { ScrambledAsciiLogo } from './components/ScrambledAsciiLogo';
import { AmbientBinaryRain } from './components/AmbientBinaryRain';

interface TerminalEntry {
  id: string;
  command?: string;
  type: 'BANNER' | 'TEXT' | 'ERROR' | 'SUCCESS' | 'HELP' | 'INSPECT' | 'TRACE' | 'LOGS' | 'GRAPH' | 'STATUS';
  content?: any;
}

export function App() {
  const [showSplash, setShowSplash] = useState<boolean>(true);

  const [inputVal, setInputVal] = useState<string>('');
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIdx, setHistoryIdx] = useState<number>(-1);
  const [entries, setEntries] = useState<TerminalEntry[]>([]);

  const inputRef = useRef<HTMLInputElement>(null);
  const scrollBottomRef = useRef<HTMLDivElement>(null);
  const terminalBodyRef = useRef<HTMLDivElement>(null);

  // Instant synchronous scroll to bottom
  const scrollToBottom = () => {
    if (terminalBodyRef.current) {
      terminalBodyRef.current.scrollTop = terminalBodyRef.current.scrollHeight;
    }
  };

  // Keep scroll locked to bottom on new entries
  useEffect(() => {
    scrollToBottom();
    const t = setTimeout(scrollToBottom, 30);
    return () => clearTimeout(t);
  }, [entries]);

  // Focus input automatically
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleRunCommand = (raw: string) => {
    const trimmed = raw.trim();
    if (!trimmed) {
      setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'TEXT', command: '' }]);
      return;
    }

    setCommandHistory(prev => [trimmed, ...prev]);
    setHistoryIdx(-1);
    scrollToBottom();
    requestAnimationFrame(scrollToBottom);

    const tokens = trimmed.split(/\s+/);
    const root = tokens[0].toLowerCase();
    const arg1 = tokens[1];
    const arg2 = tokens[2];

    sound.playKeyClick();

    switch (root) {
      case 'graph':
      case 'dashboard':
      case 'g':
      case 'nodes':
        sound.playEnterSuccess();
        setEntries(prev => [
          ...prev,
          {
            id: `entry-${Date.now()}`,
            command: trimmed,
            type: 'GRAPH'
          }
        ]);
        break;

      case 'clear':
      case 'cls':
        setEntries([]);
        sound.playEnterSuccess();
        break;

      case 'help':
      case 'man':
      case '?':
        sound.playEnterSuccess();
        setEntries(prev => [
          ...prev,
          {
            id: `entry-${Date.now()}`,
            command: trimmed,
            type: 'HELP',
            content: { filter: arg1 || null }
          }
        ]);
        break;

      case 'sound':
      case 'audio':
        {
          const nextState = arg1 === 'on' ? true : arg1 === 'off' ? false : !sound.isEnabled();
          sound.setEnabled(nextState);
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'SUCCESS',
              content: { message: `Audio synthesizer: ${nextState ? 'ENABLED' : 'MUTED'}` }
            }
          ]);
        }
        break;

      case 'reboot':
      case 'splash':
      case 'boot':
        setShowSplash(true);
        break;

      default:
        sound.playErrorChirp();
        setEntries(prev => [
          ...prev,
          {
            id: `entry-${Date.now()}`,
            command: trimmed,
            type: 'ERROR',
            content: {
              message: `bash: command not found: ${root}. Type 'help' to see available commands.`
            }
          }
        ]);
        break;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== 'Enter' && e.key !== 'Tab') {
      sound.playKeyClick();
    }

    if (e.key === 'Enter') {
      e.preventDefault();
      handleRunCommand(inputVal);
      setInputVal('');
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length > 0) {
        const nextIdx = Math.min(historyIdx + 1, commandHistory.length - 1);
        setHistoryIdx(nextIdx);
        setInputVal(commandHistory[nextIdx]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIdx > 0) {
        const prevIdx = historyIdx - 1;
        setHistoryIdx(prevIdx);
        setInputVal(commandHistory[prevIdx]);
      } else if (historyIdx === 0) {
        setHistoryIdx(-1);
        setInputVal('');
      }
    } else if (e.key === 'Tab') {
      e.preventDefault();
      // Auto complete
      const trimmed = inputVal.trim();
      if (!trimmed) return;
      const allCmds = ['graph', 'help', 'clear', 'sound', 'reboot'];
      const match = allCmds.find(c => c.startsWith(trimmed.toLowerCase()));
      if (match) {
        setInputVal(match + ' ');
      }
    } else if (e.ctrlKey && (e.key === 'l' || e.key === 'L')) {
      e.preventDefault();
      setEntries([]);
    }
  };

  return (
    <div className="terminal-window" onClick={() => inputRef.current?.focus()}>
      {/* Subtle Ambient Matrix 0/1 Falling Dust in Background */}
      <AmbientBinaryRain />

      {/* Retro Pac-Man Eating Bitcoin Splash Screen */}
      {showSplash && (
        <PacmanSplashScreen
          onComplete={() => {
            setShowSplash(false);
            setTimeout(() => inputRef.current?.focus(), 80);
          }}
        />
      )}

      {/* Clean Window Title Bar */}
      <div className="terminal-titlebar">
        <div className="window-dots">
          <span className="window-dot dot-red" />
          <span className="window-dot dot-yellow" />
          <span className="window-dot dot-green" />
        </div>
        <div style={{ fontWeight: 500 }}>bitkaun@investigation: ~ (bash)</div>
        <div style={{ fontSize: '12px', color: '#555555' }}>x86_64 tty1</div>
      </div>

      {/* Terminal Content Buffer */}
      <div ref={terminalBodyRef} className="terminal-body">
        {/* Permanent Welcome Header & Available Commands (Never Erased) */}
        <div className="output-block" style={{ borderBottom: '1px solid var(--border-mid)', paddingBottom: '14px', marginBottom: '8px' }}>
          <ScrambledAsciiLogo active={!showSplash} />

          <div style={{ color: 'var(--fg-white)', fontSize: '15px', fontWeight: 600, marginBottom: '4px' }}>
            Welcome to BitKaun? (Version 1.0.0)
          </div>
          <div style={{ color: 'var(--fg-muted)', marginBottom: '16px', fontSize: '14px' }}>
            Crypto Transaction Anomaly &amp; Forensics Engine.
            <br />
            Type <span className="cmd-tag" onClick={() => handleRunCommand('help')}>'help'</span> to see the list of available commands.
          </div>

          <div style={{ color: 'var(--fg-primary)', fontWeight: 600, marginBottom: '6px' }}>
            Available Commands:
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginBottom: '8px', color: 'var(--fg-text)' }}>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('graph')}>[graph]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('g')}>[g]</span>
              <span className="cmd-desc">- Open interactive forensic link-analysis dashboard &amp; TUI subwindows</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('help')}>[help]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('man')}>[man]</span>
              <span className="cmd-desc">- Detailed command manual and usage instructions</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('clear')}>[clear]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('cls')}>[cls]</span>
              <span className="cmd-desc">- Clear the terminal output buffer (Shortcut: Ctrl+L)</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('sound')}>[sound]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('audio')}>[audio]</span>
              <span className="cmd-desc">- Toggle procedural mechanical keyboard &amp; arcade audio (on/off)</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('reboot')}>[reboot]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('splash')}>[splash]</span>
              <span className="cmd-desc">- Replay Pac-Man Bitcoin arcade startup sequence</span>
            </div>
          </div>
        </div>

        {/* Dynamic Command Outputs */}
        {entries.map(entry => (
          <div key={entry.id}>
            {/* Command line if typed by user */}
            {entry.command !== undefined && (
              <div className="prompt-line" style={{ marginBottom: '4px' }}>
                <span className="prompt-prefix">bitkaun@investigation</span>
                <span className="prompt-char">:$</span>
                <span style={{ color: 'var(--fg-white)' }}>{entry.command}</span>
              </div>
            )}

            {/* Animated CLI Output Stream */}
            <CliOutputRenderer
              entry={entry}
              onRunCommand={handleRunCommand}
              onScrollRequested={scrollToBottom}
              onCloseEntry={(id) => setEntries(prev => prev.filter(e => e.id !== id))}
            />
          </div>
        ))}

        {/* Current Active Input Prompt */}
        <div className="prompt-line">
          <span className="prompt-prefix">bitkaun@investigation</span>
          <span className="prompt-char">:$</span>
          <div className="input-cursor-wrapper">
            <span className="typed-text">{inputVal}</span>
            <span className="cli-cursor" />
            <input
              ref={inputRef}
              type="text"
              className="terminal-real-input"
              value={inputVal}
              onChange={e => setInputVal(e.target.value)}
              onKeyDown={handleKeyDown}
              autoFocus
              spellCheck={false}
              autoComplete="off"
            />
          </div>
        </div>

        <div ref={scrollBottomRef} />
      </div>
    </div>
  );
}

export default App;
