import React, { useState, useEffect, useRef } from 'react';
import { sound } from './audio/soundEngine';
import { CliOutputRenderer } from './components/CliOutputRenderer';
import { PacmanSplashScreen } from './components/PacmanSplashScreen';
import { ScrambledAsciiLogo } from './components/ScrambledAsciiLogo';
import { AmbientBinaryRain } from './components/AmbientBinaryRain';
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
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIdx, setHistoryIdx] = useState<number>(-1);
  const [entries, setEntries] = useState<TerminalEntry[]>([]);

  const inputRef = useRef<HTMLInputElement>(null);
  const scrollBottomRef = useRef<HTMLDivElement>(null);
  const terminalBodyRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (terminalBodyRef.current) {
      terminalBodyRef.current.scrollTop = terminalBodyRef.current.scrollHeight;
    }
  };

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
        try {
          // Check if numeric txid or address
          const isNumeric = /^\d+$/.test(arg1);
          if (isNumeric) {
            const tx = await api.getTransaction(arg1);
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
                    riskScore: 65,
                    clusterId: tx.scenario_id,
                    balanceBtc: tx.output_amounts ? tx.output_amounts.reduce((a, b) => a + b, 0) : 0,
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
                    riskScore: entity.is_licit_exchange ? 10 : 60,
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
              content: { message: "Usage: taint <seed_address> (e.g. 'taint 12dhqUGwzF6c6eW5F7DkyXyqBmW1')" }
            }
          ]);
          return;
        }
        sound.playEnterSuccess();
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
        }
        break;

      case 'alerts':
      case 'alert':
        sound.playEnterSuccess();
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
              content: { message: "Usage: dossier <txid> (e.g. 'dossier 58234917')" }
            }
          ]);
          return;
        }
        sound.playEnterSuccess();
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
        }
        break;

      case 'tor':
        sound.playEnterSuccess();
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
        }
        break;

      case 'status':
      case 'sys':
      case 'health':
        sound.playEnterSuccess();
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
      const trimmed = inputVal.trim();
      if (!trimmed) return;
      const allCmds = ['graph', 'inspect', 'trace', 'taint', 'alerts', 'dossier', 'tor', 'status', 'help', 'clear', 'sound', 'reboot'];
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
