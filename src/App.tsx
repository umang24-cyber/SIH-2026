import React, { useState, useEffect, useRef, useCallback } from 'react';
import { sound } from './audio/soundEngine';
import { CliOutputRenderer } from './components/CliOutputRenderer';
import { PacmanSplashScreen } from './components/PacmanSplashScreen';
import { ScrambledAsciiLogo } from './components/ScrambledAsciiLogo';
import { AmbientBinaryRain } from './components/AmbientBinaryRain';
import { CliSpinner } from './components/CliSpinner';
import { api } from './services/api';

interface TerminalEntry {
  id: string;
  command?: string;
  type: 'BANNER' | 'TEXT' | 'ERROR' | 'SUCCESS' | 'HELP' | 'INSPECT' | 'TRACE' | 'LOGS' | 'GRAPH' | 'STATUS' | 'ALERTS' | 'TAINT' | 'DOSSIER' | 'TOR';
  content?: any;
}

export function App() {
  const [showSplash, setShowSplash] = useState<boolean>(true);
  const [inputVal, setInputVal] = useState<string>('');
  const [cursorPos, setCursorPos] = useState<number>(0);
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIdx, setHistoryIdx] = useState<number>(-1);
  const [entries, setEntries] = useState<TerminalEntry[]>([]);
  const [pendingCommand, setPendingCommand] = useState<string | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const scrollBottomRef = useRef<HTMLDivElement>(null);
  const terminalBodyRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    if (terminalBodyRef.current) {
      terminalBodyRef.current.scrollTop = terminalBodyRef.current.scrollHeight;
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
    const t = setTimeout(scrollToBottom, 30);
    return () => clearTimeout(t);
  }, [entries]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleRunCommand = async (raw: string) => {
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
            type: 'GRAPH',
            content: { scenarioId: arg1 || 'licit_00001' }
          }
        ]);
        break;

      case 'inspect':
      case 'i':
        if (!arg1) {
          sound.playErrorChirp();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'ERROR',
              content: { message: "Usage: inspect <txid | address> (e.g. 'inspect 58234917' or 'inspect 12dhqUGwzF6c6eW5F7DkyXyqBmW1')" }
            }
          ]);
          return;
        }
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
        try {
          // Check if numeric txid or address
          const isNumeric = /^\d+$/.test(arg1);
          if (isNumeric) {
            const tx = await api.getTransaction(arg1);
            const isIllicit = tx.scenario_id && !tx.scenario_id.toLowerCase().startsWith('licit');
            const risk = isIllicit ? (tx.scenario_id.includes('ransom') ? 92 : 78) : 15;

            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'INSPECT',
                content: {
                  id: `TX:${arg1}`,
                  raw: tx,
                  node: {
                    id: `TX:${arg1}`,
                    label: `TX:${arg1} (Scenario: ${tx.scenario_id})`,
                    type: 'TRANSACTION',
                    riskScore: risk,
                    clusterId: tx.scenario_id,
                    balanceBtc: tx.output_amounts ? tx.output_amounts.reduce((a: number, b: number) => a + b, 0) : 0,
                    txCount: 1,
                    firstSeen: tx.timestamp,
                    lastSeen: tx.timestamp,
                    tags: [tx.script_type, tx.network?.node_type || 'standard_relay'],
                    flags: tx.network?.node_type?.includes('tor') ? ['TOR_EXIT_NODE'] : []
                  }
                }
              }
            ]);
          } else {
            const entity = await api.getEntity(arg1);
            let clusterId = 'UNCLUSTERED';
            try {
              const cl = await api.getEntityCluster(arg1);
              clusterId = cl.cluster_id;
            } catch {}

            const isIllicit = entity.associated_scenarios?.some((sc: string) => !sc.toLowerCase().startsWith('licit'));
            const risk = entity.is_licit_exchange ? 5 : isIllicit ? 85 : 20;

            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'INSPECT',
                content: {
                  id: arg1,
                  raw: entity,
                  node: {
                    id: arg1,
                    label: entity.address,
                    type: entity.is_licit_exchange ? 'EXCHANGE' : 'WALLET',
                    riskScore: risk,
                    clusterId: clusterId,
                    balanceBtc: entity.total_received_btc - entity.total_sent_btc,
                    txCount: entity.tx_count,
                    firstSeen: entity.first_seen,
                    lastSeen: entity.last_seen,
                    tags: entity.associated_scenarios,
                    flags: entity.is_licit_exchange ? ['LICIT_EXCHANGE_WHITELIST'] : ['SUSPECT_P2P_WALLET'],
                    isLicitExchange: entity.is_licit_exchange
                  }
                }
              }
            ]);
          }
        } catch (err: any) {
          sound.playErrorChirp();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'ERROR',
              content: { message: `Inspect failed: ${err.message}` }
            }
          ]);
        } finally {
          setPendingCommand(null);
        }
        break;

      case 'trace':
      case 'route':
        if (!arg1 || !arg2) {
          sound.playErrorChirp();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'ERROR',
              content: { message: "Usage: trace <source_address> <target_address>" }
            }
          ]);
          return;
        }
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
        try {
          const traceResult = await api.getTrace(arg1, arg2);
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'TRACE',
              content: { source: arg1, target: arg2, traceResult }
            }
          ]);
        } catch (err: any) {
          sound.playErrorChirp();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'ERROR',
              content: { message: `Trace failed: ${err.message}` }
            }
          ]);
        } finally {
          setPendingCommand(null);
        }
        break;

      case 'taint':
        if (!arg1) {
          sound.playErrorChirp();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'ERROR',
              content: { message: "Usage: taint <seed_address> (e.g. 'taint 18hvz1KnqUjLRr3KHifSbMDi6m')" }
            }
          ]);
          return;
        }
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
        try {
          const taintRes = await api.getTaint(arg1);
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'TAINT',
              content: taintRes
            }
          ]);
        } catch (err: any) {
          sound.playErrorChirp();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'ERROR',
              content: { message: `Taint propagation failed: ${err.message}` }
            }
          ]);
        } finally {
          setPendingCommand(null);
        }
        break;

      case 'alerts':
      case 'alert':
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
        try {
          const alertsRes = await api.getAlerts(0.5, 20);
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'ALERTS',
              content: alertsRes
            }
          ]);
        } catch (err: any) {
          sound.playErrorChirp();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'ERROR',
              content: { message: `Alerts retrieval failed: ${err.message}` }
            }
          ]);
        } finally {
          setPendingCommand(null);
        }
        break;

      case 'dossier':
      case 'report':
        if (!arg1) {
          sound.playErrorChirp();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'ERROR',
              content: { message: "Usage: dossier <txid> (e.g. 'dossier 322596997')" }
            }
          ]);
          return;
        }
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
        try {
          const dossierRes = await api.getDossier(arg1);
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'DOSSIER',
              content: dossierRes
            }
          ]);
        } catch (err: any) {
          sound.playErrorChirp();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'ERROR',
              content: { message: `Dossier generation failed: ${err.message}` }
            }
          ]);
        } finally {
          setPendingCommand(null);
        }
        break;

      case 'tor':
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
        try {
          if (arg1) {
            const torProf = await api.getTorProfiler(arg1);
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'TOR',
                content: torProf
              }
            ]);
          } else {
            const torSum = await api.getTorSummary();
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'TOR',
                content: torSum
              }
            ]);
          }
        } catch (err: any) {
          sound.playErrorChirp();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'ERROR',
              content: { message: `Tor profiler failed: ${err.message}` }
            }
          ]);
        } finally {
          setPendingCommand(null);
        }
        break;

      case 'logs':
      case 'log':
      case 'stream':
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
        try {
          const batch = await api.getStreamBatch(15);
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'LOGS',
              content: batch
            }
          ]);
        } catch (err: any) {
          sound.playErrorChirp();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'ERROR',
              content: { message: `Stream telemetry failed: ${err.message}` }
            }
          ]);
        } finally {
          setPendingCommand(null);
        }
        break;

      case 'status':
      case 'sys':
      case 'health':
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
        try {
          const health = await api.getHealth();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'STATUS',
              content: health
            }
          ]);
        } catch (err: any) {
          sound.playErrorChirp();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'ERROR',
              content: { message: `Engine offline or unreachable: ${err.message}` }
            }
          ]);
        } finally {
          setPendingCommand(null);
        }
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

  const syncCursorPos = (target: HTMLInputElement | null) => {
    if (!target) return;
    const pos = target.selectionStart ?? target.value.length;
    setCursorPos(pos);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== 'Enter' && e.key !== 'Tab') {
      sound.playKeyClick();
    }

    if (e.key === 'Enter') {
      e.preventDefault();
      handleRunCommand(inputVal);
      setInputVal('');
      setCursorPos(0);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length > 0) {
        const nextIdx = Math.min(historyIdx + 1, commandHistory.length - 1);
        setHistoryIdx(nextIdx);
        const val = commandHistory[nextIdx];
        setInputVal(val);
        setCursorPos(val.length);
        setTimeout(() => {
          if (inputRef.current) {
            inputRef.current.setSelectionRange(val.length, val.length);
          }
        }, 0);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIdx > 0) {
        const prevIdx = historyIdx - 1;
        setHistoryIdx(prevIdx);
        const val = commandHistory[prevIdx];
        setInputVal(val);
        setCursorPos(val.length);
        setTimeout(() => {
          if (inputRef.current) {
            inputRef.current.setSelectionRange(val.length, val.length);
          }
        }, 0);
      } else if (historyIdx === 0) {
        setHistoryIdx(-1);
        setInputVal('');
        setCursorPos(0);
      }
    } else if (e.key === 'Tab') {
      e.preventDefault();
      const trimmed = inputVal.trim();
      if (!trimmed) return;
      const allCmds = ['graph', 'inspect', 'trace', 'taint', 'alerts', 'dossier', 'tor', 'status', 'help', 'clear', 'sound', 'reboot'];
      const match = allCmds.find(c => c.startsWith(trimmed.toLowerCase()));
      if (match) {
        const completed = match + ' ';
        setInputVal(completed);
        setCursorPos(completed.length);
        setTimeout(() => {
          if (inputRef.current) {
            inputRef.current.setSelectionRange(completed.length, completed.length);
          }
        }, 0);
      }
    } else if (e.ctrlKey && (e.key === 'l' || e.key === 'L')) {
      e.preventDefault();
      setEntries([]);
    } else if (['ArrowLeft', 'ArrowRight', 'Home', 'End', 'Backspace', 'Delete'].includes(e.key)) {
      requestAnimationFrame(() => syncCursorPos(inputRef.current));
    }
  };

  const safeCursorPos = Math.max(0, Math.min(cursorPos, inputVal.length));
  const textBefore = inputVal.slice(0, safeCursorPos);
  const charAtCursor = inputVal.slice(safeCursorPos, safeCursorPos + 1);
  const textAfter = inputVal.slice(safeCursorPos + 1);

  return (
    <div className="terminal-window" onClick={() => inputRef.current?.focus()}>
      <AmbientBinaryRain />

      {showSplash && (
        <PacmanSplashScreen
          onComplete={() => {
            setShowSplash(false);
            setTimeout(() => inputRef.current?.focus(), 80);
          }}
        />
      )}

      {/* Title Bar */}
      <div className="terminal-titlebar">
        <div className="window-dots">
          <span className="window-dot dot-red" />
          <span className="window-dot dot-yellow" />
          <span className="window-dot dot-green" />
        </div>
        <div style={{ fontWeight: 500 }}>bitkaun@investigation: ~ (bash)</div>
        <div style={{ fontSize: '12px', color: '#555555' }}>x86_64 tty1 [FASTAPI LINKED]</div>
      </div>

      {/* Terminal Content Buffer */}
      <div ref={terminalBodyRef} className="terminal-body">
        {/* Permanent Welcome Header & Available Commands */}
        <div className="output-block" style={{ borderBottom: '1px solid var(--border-mid)', paddingBottom: '14px', marginBottom: '8px' }}>
          <ScrambledAsciiLogo active={!showSplash} />

          <div style={{ color: 'var(--fg-white)', fontSize: '15px', fontWeight: 600, marginBottom: '4px' }}>
            Welcome to BitKaun? (Version 1.0.0 · Air-Gapped Engine)
          </div>
          <div style={{ color: 'var(--fg-muted)', marginBottom: '16px', fontSize: '14px' }}>
            Bitcoin Cross-Layer AML Forensics &amp; Dual-Stream Telemetry Correlation.
            <br />
            Type <span className="cmd-tag" onClick={() => handleRunCommand('help')}>'help'</span> to see all forensic commands.
          </div>

          <div style={{ color: 'var(--fg-primary)', fontWeight: 600, marginBottom: '6px' }}>
            Interactive Commands (Click to Run):
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '6px', marginBottom: '8px', color: 'var(--fg-text)', fontSize: '14px' }}>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('status')}>[status]</span>
              <span className="cmd-desc"> - Memory engine diagnostics</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('graph')}>[graph]</span>
              <span className="cmd-desc"> - 3D/2D visual graph explorer</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('alerts')}>[alerts]</span>
              <span className="cmd-desc"> - Typology alert feed</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('tor')}>[tor]</span>
              <span className="cmd-desc"> - Tor timing entropy profiler</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('help')}>[help]</span>
              <span className="cmd-desc"> - Detailed command manual</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('clear')}>[clear]</span>
              <span className="cmd-desc"> - Clear screen (Ctrl+L)</span>
            </div>
          </div>
        </div>

        {/* Dynamic Command Outputs */}
        {entries.map(entry => (
          <div key={entry.id}>
            {entry.command !== undefined && (
              <div className="prompt-line" style={{ marginBottom: '4px' }}>
                <span className="prompt-prefix">bitkaun@investigation</span>
                <span className="prompt-char">:$</span>
                <span style={{ color: 'var(--fg-white)' }}>{entry.command}</span>
              </div>
            )}

            <CliOutputRenderer
              entry={entry}
              onRunCommand={handleRunCommand}
              onScrollRequested={scrollToBottom}
              onCloseEntry={(id) => setEntries(prev => prev.filter(e => e.id !== id))}
            />
          </div>
        ))}

        {/* Active Command Execution Spinner */}
        {pendingCommand && (
          <div style={{ margin: '8px 0', padding: '4px 0', color: '#00ff66', fontFamily: 'monospace' }}>
            <CliSpinner label={`EXECUTING COMMAND: [${pendingCommand}] ...`} />
          </div>
        )}

        {/* Current Active Input Prompt */}
        <div className="prompt-line">
          <span className="prompt-prefix">bitkaun@investigation</span>
          <span className="prompt-char">:$</span>
          <div className="input-cursor-wrapper">
            <span className="typed-text">{textBefore}</span>
            <span key={safeCursorPos} className="cli-cursor">
              {charAtCursor || '\u00A0'}
            </span>
            <span className="typed-text">{textAfter}</span>
            <input
              ref={inputRef}
              type="text"
              className="terminal-real-input"
              value={inputVal}
              onChange={e => {
                setInputVal(e.target.value);
                setCursorPos(e.target.selectionStart ?? e.target.value.length);
              }}
              onKeyDown={handleKeyDown}
              onKeyUp={e => syncCursorPos(e.currentTarget)}
              onClick={e => syncCursorPos(e.currentTarget)}
              onSelect={e => syncCursorPos(e.currentTarget)}
              onFocus={e => syncCursorPos(e.currentTarget)}
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
