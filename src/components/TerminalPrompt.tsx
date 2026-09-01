import React, { useState, useRef, useEffect } from 'react';
import { TerminalHistoryItem } from '../types/terminal';
import { COMMAND_REGISTRY } from '../data/mockForensicData';
import { sound } from '../audio/soundEngine';

interface TerminalPromptProps {
  history: TerminalHistoryItem[];
  knownNodeIds: string[];
  onExecuteCommand: (cmd: string) => void;
}

export const TerminalPrompt: React.FC<TerminalPromptProps> = ({
  history,
  knownNodeIds,
  onExecuteCommand
}) => {
  const [inputVal, setInputVal] = useState<string>('');
  const [historyIndex, setHistoryIndex] = useState<number>(-1);
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const historyContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll terminal history to bottom
  useEffect(() => {
    if (historyContainerRef.current) {
      historyContainerRef.current.scrollTop = historyContainerRef.current.scrollHeight;
    }
  }, [history]);

  // Keep input focused
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    // Keystroke sound
    if (e.key !== 'Enter' && e.key !== 'Tab') {
      sound.playKeyClick();
    }

    if (e.key === 'Enter') {
      e.preventDefault();
      const trimmed = inputVal.trim();
      if (trimmed) {
        setCommandHistory(prev => [trimmed, ...prev]);
        setHistoryIndex(-1);
        onExecuteCommand(trimmed);
        setInputVal('');
      } else {
        onExecuteCommand('');
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length > 0) {
        const nextIdx = Math.min(historyIndex + 1, commandHistory.length - 1);
        setHistoryIndex(nextIdx);
        setInputVal(commandHistory[nextIdx]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex > 0) {
        const prevIdx = historyIndex - 1;
        setHistoryIndex(prevIdx);
        setInputVal(commandHistory[prevIdx]);
      } else if (historyIndex === 0) {
        setHistoryIndex(-1);
        setInputVal('');
      }
    } else if (e.key === 'Tab') {
      e.preventDefault();
      handleAutoComplete();
    } else if (e.ctrlKey && (e.key === 'l' || e.key === 'L')) {
      e.preventDefault();
      onExecuteCommand('clear');
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setInputVal('');
    }
  };

  const handleAutoComplete = () => {
    const trimmed = inputVal.trim();
    if (!trimmed) return;

    const parts = trimmed.split(' ');
    
    // Command autocompletion
    if (parts.length === 1) {
      const allCmds: string[] = [];
      COMMAND_REGISTRY.forEach(c => {
        allCmds.push(c.name);
        allCmds.push(...c.aliases);
      });

      const matches = allCmds.filter(c => c.toLowerCase().startsWith(parts[0].toLowerCase()));
      if (matches.length === 1) {
        setInputVal(matches[0] + ' ');
      } else if (matches.length > 1) {
        // Show suggestions in history
        sound.playKeyClick();
      }
    } else if (parts.length >= 2) {
      // Node ID autocompletion
      const lastPart = parts[parts.length - 1];
      const matches = knownNodeIds.filter(id => id.toLowerCase().startsWith(lastPart.toLowerCase()));
      if (matches.length === 1) {
        parts[parts.length - 1] = matches[0];
        setInputVal(parts.join(' ') + ' ');
      }
    }
  };

  return (
    <div
      className="tty-cli-pane"
      onClick={() => inputRef.current?.focus()}
      role="region"
      aria-label="Terminal Shell Command Buffer"
    >
      <div className="tty-history-list" ref={historyContainerRef}>
        {history.map(item => {
          let lineClass = 'history-line-success';
          if (item.type === 'INPUT') lineClass = 'history-line-input';
          if (item.type === 'ERROR') lineClass = 'history-line-error';
          if (item.type === 'INFO') lineClass = 'history-line-info';
          if (item.type === 'SYS') lineClass = 'history-line-sys';

          return (
            <div key={item.id} className={lineClass} style={{ wordBreak: 'break-word' }}>
              {item.clickableCmd ? (
                <span
                  className="cmd-clickable"
                  onClick={(e) => {
                    e.stopPropagation();
                    onExecuteCommand(item.clickableCmd!);
                  }}
                >
                  {item.text}
                </span>
              ) : (
                <span>{item.text}</span>
              )}
            </div>
          );
        })}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', marginTop: '2px' }}>
        <span style={{ color: '#00ff66', fontWeight: 'bold', flexShrink: 0 }}>
          bitkaun@investigation:~#&nbsp;
        </span>
        <input
          ref={inputRef}
          type="text"
          className="tty-input"
          value={inputVal}
          onChange={e => setInputVal(e.target.value)}
          onKeyDown={handleKeyDown}
          autoFocus
          spellCheck={false}
          autoComplete="off"
        />
        <span className="terminal-cursor" />
      </div>
    </div>
  );
};
