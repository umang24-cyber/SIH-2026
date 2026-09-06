import React, { useState, useEffect, useRef } from 'react';
<<<<<<< HEAD
=======
import { ForensicNode, ForensicLink, KernelLogEntry } from './types/terminal';
import {
  INITIAL_NODES,
  INITIAL_LINKS,
  INITIAL_LOGS,
  COMMAND_REGISTRY,
  MOCK_HEX_DUMPS,
  GRAPH_METADATA,
  CANDIDATE_INDEX
} from './data/forensicData';
import { GraphView3D } from './components/views/GraphView3D';
>>>>>>> origin/graph
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
<<<<<<< HEAD
  const [showSplash, setShowSplash] = useState<boolean>(true);
=======
  const [nodes] = useState<ForensicNode[]>(INITIAL_NODES);
  const [links] = useState<ForensicLink[]>(INITIAL_LINKS);
  const [logs] = useState<KernelLogEntry[]>(INITIAL_LOGS);

>>>>>>> origin/graph
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

<<<<<<< HEAD
=======
      case 'graph':
      case 'nodes':
      case 'g':
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

      case 'inspect':
      case 'cat':
      case 'hex':
      case 'view':
        {
          const targetId = arg1 || '1PTqbgVoXSbuzQKrDGw2M2tchx';
          // Find matching wallet or candidate
          const matchNode = nodes.find(
            n => n.id.toLowerCase() === targetId.toLowerCase() ||
                 n.candidateId?.toLowerCase() === targetId.toLowerCase()
          );

          if (matchNode) {
            sound.playEnterSuccess();
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'INSPECT',
                content: { node: matchNode }
              }
            ]);
          } else {
            // Check candidate index
            const matchCand = CANDIDATE_INDEX.find(c => c.candidate_id.toLowerCase() === targetId.toLowerCase());
            if (matchCand) {
              const seedNode = nodes.find(n => n.id === matchCand.origin) || nodes[0];
              sound.playEnterSuccess();
              setEntries(prev => [
                ...prev,
                {
                  id: `entry-${Date.now()}`,
                  command: trimmed,
                  type: 'INSPECT',
                  content: { node: seedNode, candidate: matchCand }
                }
              ]);
            } else {
              sound.playErrorChirp();
              setEntries(prev => [
                ...prev,
                {
                  id: `entry-${Date.now()}`,
                  command: trimmed,
                  type: 'ERROR',
                  content: {
                    message: `Entity not found: '${targetId}'. Try inspecting: 1PTqbgVoXSbuzQKrDGw2M2tchx or 17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G`
                  }
                }
              ]);
            }
          }
        }
        break;

      case 'trace':
      case 'tr':
      case 'path':
      case 'flow':
        {
          // Supports: trace <cand_id> or trace <src> <dst>
          let candidateId = 'peel_0564';
          let src = '1PTqbgVoXSbuzQKrDGw2M2tchx';
          let dst = '1s6D1TaSbKqeTG5YMhWWRJ85Ve8s7Y';

          if (arg1 && arg1.toLowerCase().startsWith('peel_')) {
            candidateId = arg1;
            src = '1PTqbgVoXSbuzQKrDGw2M2tchx';
            dst = '1s6D1TaSbKqeTG5YMhWWRJ85Ve8s7Y';
          } else if (arg1 && arg1.toLowerCase().startsWith('layer_')) {
            candidateId = arg1;
            src = '17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G';
            dst = '1JadLZMcaFX1JvRTkHmcAEZ4ygHm';
          } else if (arg1 && arg1.toLowerCase().startsWith('mix_')) {
            candidateId = arg1;
            src = 'mix_cluster';
            dst = 'coinjoin_pool';
          } else if (arg1 && arg2) {
            src = arg1;
            dst = arg2;
            candidateId = 'custom';
          }

          sound.playEnterSuccess();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'TRACE',
              content: { src, dst, candidateId }
            }
          ]);
        }
        break;

      case 'dmesg':
      case 'logs':
      case 'd':
        sound.playEnterSuccess();
        setEntries(prev => [
          ...prev,
          {
            id: `entry-${Date.now()}`,
            command: trimmed,
            type: 'LOGS'
          }
        ]);
        break;

      case 'home':
      case 'banner':
      case 'cd':
        sound.playEnterSuccess();
        setEntries(prev => [
          ...prev,
          {
            id: `entry-${Date.now()}`,
            command: trimmed,
            type: 'BANNER'
          }
        ]);
        break;

      case 'status':
      case 'top':
      case 'whoami':
        sound.playEnterSuccess();
        setEntries(prev => [
          ...prev,
          {
            id: `entry-${Date.now()}`,
            command: trimmed,
            type: 'STATUS'
          }
        ]);
        break;

>>>>>>> origin/graph
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
<<<<<<< HEAD
        <div style={{ fontWeight: 500 }}>bitkaun@investigation: ~ (bash)</div>
        <div style={{ fontSize: '12px', color: '#555555' }}>x86_64 tty1 [FASTAPI LINKED]</div>
      </div>

      {/* Terminal Content Buffer */}
      <div ref={terminalBodyRef} className="terminal-body">
=======
        <div style={{ fontWeight: 500 }}>bitkaun@investigation: ~ (bash - SIH PS 146)</div>
        <div style={{ fontSize: '12px', color: '#555555' }}>x86_64 tty1 [AIR-GAPPED OFFLINE]</div>
      </div>

      {/* Terminal Content Buffer */}
      <div className="terminal-body">
>>>>>>> origin/graph
        {/* Permanent Welcome Header & Available Commands */}
        <div className="output-block" style={{ borderBottom: '1px solid var(--border-mid)', paddingBottom: '14px', marginBottom: '8px' }}>
          <ScrambledAsciiLogo active={!showSplash} />

          <div style={{ color: 'var(--fg-white)', fontSize: '15px', fontWeight: 600, marginBottom: '4px' }}>
<<<<<<< HEAD
            Welcome to BitKaun? (Version 1.0.0 · Air-Gapped Engine)
          </div>
          <div style={{ color: 'var(--fg-muted)', marginBottom: '16px', fontSize: '14px' }}>
            Bitcoin Cross-Layer AML Forensics &amp; Dual-Stream Telemetry Correlation.
            <br />
            Type <span className="cmd-tag" onClick={() => handleRunCommand('help')}>'help'</span> to see all forensic commands.
=======
            Welcome to BitKaun? (Bitcoin AML Forensics Console v6.2)
          </div>
          <div style={{ color: 'var(--fg-muted)', marginBottom: '16px', fontSize: '14px' }}>
            SIH PS 146: AI-Powered Monitoring &amp; Analysis of Bitcoin Transaction Traffic.
            <br />
            Type <span className="cmd-tag" onClick={() => handleRunCommand('help')}>'help'</span> to view forensic manual. Fully offline execution verified.
>>>>>>> origin/graph
          </div>

          <div style={{ color: 'var(--fg-primary)', fontWeight: 600, marginBottom: '6px' }}>
            Interactive Commands (Click to Run):
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '6px', marginBottom: '8px', color: 'var(--fg-text)', fontSize: '14px' }}>
            <div>
<<<<<<< HEAD
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
=======
              <span className="cmd-tag" onClick={() => handleRunCommand('graph')}>[graph]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('g')}>[g]</span>
              <span className="cmd-desc">- 3D WebGL Force Graph of Bitcoin wallets, peeling chains &amp; layering routes</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('inspect 1PTqbgVoXSbuzQKrDGw2M2tchx')}>[inspect &lt;address&gt;]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('cat')}>[cat]</span>
              <span className="cmd-desc">- Inspect Bitcoin entity dossier, AML risk score, ASN &amp; script bytecode</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('trace peel_0564')}>[trace &lt;cand_id | src dst&gt;]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('tr')}>[tr]</span>
              <span className="cmd-desc">- Reconstruct multi-hop UTXO peeling flow or fan-out layering branches</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('dmesg')}>[dmesg]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('logs')}>[logs]</span>
              <span className="cmd-desc">- Stream live V6 graph detector intercepts &amp; ML classification confidence</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('status')}>[status]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('top')}>[top]</span>
              <span className="cmd-desc">- Graph engine telemetry (459k nodes, 527k edges, 3,531 candidates)</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('clear')}>[clear]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('cls')}>[cls]</span>
              <span className="cmd-desc">- Clear terminal history buffer (Shortcut: Ctrl+L)</span>
            </div>
          </div>

          <div style={{ color: 'var(--fg-primary)', fontWeight: 600, marginBottom: '6px' }}>
            Quick Forensic Queries (True Positive Verified Candidates):
          </div>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <span className="cmd-tag" onClick={() => handleRunCommand('trace peel_0564')}>
              [trace peel_0564]
            </span>
            <span className="cmd-tag" onClick={() => handleRunCommand('trace layer_1054')}>
              [trace layer_1054]
            </span>
            <span className="cmd-tag" onClick={() => handleRunCommand('inspect 1PTqbgVoXSbuzQKrDGw2M2tchx')}>
              [inspect 1PTqbgVoXSbuzQKrDGw2M2tchx]
            </span>
            <span className="cmd-tag" onClick={() => handleRunCommand('inspect 17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G')}>
              [inspect 17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G]
            </span>
>>>>>>> origin/graph
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

<<<<<<< HEAD
            <CliOutputRenderer
              entry={entry}
              onRunCommand={handleRunCommand}
              onScrollRequested={scrollToBottom}
              onCloseEntry={(id) => setEntries(prev => prev.filter(e => e.id !== id))}
            />
=======
            {/* Entry Content Rendering */}

            {entry.type === 'HELP' && (
              <div className="output-block" style={{ color: 'var(--fg-text)' }}>
                <div style={{ color: 'var(--fg-primary)', fontWeight: 600, marginBottom: '6px' }}>
                  BITKAUN MANUAL (1) - BITCOIN AML COMMAND REGISTRY
                </div>
                <table className="cli-table">
                  <thead>
                    <tr>
                      <th style={{ width: '25%' }}>Command</th>
                      <th style={{ width: '15%' }}>Alias</th>
                      <th style={{ width: '60%' }}>Description &amp; Example</th>
                    </tr>
                  </thead>
                  <tbody>
                    {COMMAND_REGISTRY.map(cmd => (
                      <tr key={cmd.name}>
                        <td style={{ color: '#38ef7d', fontWeight: 500 }}>
                          <span className="cmd-tag" onClick={() => handleRunCommand(cmd.name)}>
                            {cmd.name}
                          </span>
                        </td>
                        <td style={{ color: '#888888' }}>{cmd.aliases.join(', ')}</td>
                        <td>
                          <div>{cmd.summary}</div>
                          <div style={{ color: '#00ff66', fontSize: '13px', marginTop: '2px' }}>
                            Try:&nbsp;
                            <span className="cmd-tag" onClick={() => handleRunCommand(cmd.examples[0])}>
                              {cmd.examples[0]}
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {entry.type === 'GRAPH' && (
              <div className="output-block">
                <div style={{ color: '#00ff66', marginBottom: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>&gt; 3D Force-Directed Graph mounted (Frozen V6 AML Graph: 459k nodes context)</span>
                  <span style={{ fontSize: '12px', color: '#888888' }}>[Drag to rotate | Scroll to zoom | Click to inspect]</span>
                </div>
                <div className="graph-container-box">
                  <GraphView3D
                    nodes={nodes}
                    links={links}
                    onSelectNode={(id) => handleRunCommand(`inspect ${id}`)}
                    onRunCommand={handleRunCommand}
                  />
                </div>
              </div>
            )}

            {entry.type === 'INSPECT' && (
              <div className="output-block" style={{ color: '#dddddd' }}>
                {(() => {
                  const node = entry.content.node as ForensicNode;
                  const hex = MOCK_HEX_DUMPS[node.id] || [
                    '00000000  02 00 00 00 01 a1 b2 c3 d4 e5 f6 a7  00 00 00 00 00 00 00 00  |.....BitcoinTx..|',
                    '00000010  6a 47 30 44 02 20 1b 4c 8e 99 a0 14  00 00 00 00 00 00 00 00  |jG0D. .L........|',
                    '00000020  76 a9 14 b2 c3 d4 e5 f6 a7 b8 c9 d0  88 ac 00 00 00 00 00 00  |v.........OP_CKV|'
                  ];
                  return (
                    <div>
                      <div style={{ color: '#00ff66', fontWeight: 600, marginBottom: '6px' }}>
                        BITCOIN ENTITY DOSSIER: {node.id} ({node.label})
                      </div>
                      <table className="cli-table">
                        <tbody>
                          <tr>
                            <td style={{ color: '#888888', width: '20%' }}>Entity Role</td>
                            <td style={{ color: '#ffffff' }}>{node.type}</td>
                            <td style={{ color: '#888888', width: '20%' }}>AML Risk Score</td>
                            <td style={{ color: node.riskScore >= 80 ? '#ef4444' : '#22c55e', fontWeight: 'bold' }}>
                              {node.riskScore}/100 {node.riskScore >= 80 ? '(CRITICAL THREAT)' : '(LOW RISK)'}
                            </td>
                          </tr>
                          <tr>
                            <td style={{ color: '#888888' }}>Cluster Affiliation</td>
                            <td style={{ color: '#38bdf8' }}>{node.clusterId}</td>
                            <td style={{ color: '#888888' }}>UTXO Balance</td>
                            <td style={{ color: '#38ef7d' }}>{node.balanceBtc} BTC ({node.txCount} txs)</td>
                          </tr>
                          <tr>
                            <td style={{ color: '#888888' }}>Infrastructure</td>
                            <td style={{ color: '#a0e2bf' }}>{node.asn || 'AS13335'} ({node.relayIp || '12.10.139.26'})</td>
                            <td style={{ color: '#888888' }}>Attribution</td>
                            <td style={{ color: '#f59e0b' }}>{node.ownerAlias || 'Anonymous Entity'}</td>
                          </tr>
                          <tr>
                            <td style={{ color: '#888888' }}>Heuristic Flags</td>
                            <td colSpan={3} style={{ color: '#f59e0b' }}>
                              {node.flags.join(' | ')}
                            </td>
                          </tr>
                        </tbody>
                      </table>

                      <div style={{ fontSize: '13px', color: '#888888', marginTop: '6px', marginBottom: '2px' }}>
                        Bitcoin Script Bytecode Hexdump (/proc/bitkaun/raw_tx/{node.id.slice(0, 10)}):
                      </div>
                      <pre style={{ color: '#22c55e', fontSize: '12px', background: '#080808', padding: '8px', border: '1px solid #1a1a1a' }}>
                        {hex.join('\n')}
                      </pre>
                    </div>
                  );
                })()}
              </div>
            )}

            {entry.type === 'TRACE' && (
              <div className="output-block" style={{ color: '#dddddd' }}>
                <div style={{ color: '#00ff66', fontWeight: 600, marginBottom: '6px' }}>
                  {entry.content.candidateId === 'layer_1054'
                    ? 'FAN-OUT / FAN-IN LAYERING RECONVERGENCE TRACE :: layer_1054 (14 Parallel Routes)'
                    : entry.content.candidateId.startsWith('mix_')
                    ? 'COINJOIN BIPARTITE CO-SIGNING TRACE :: mix_0755 (Louvain Community Cluster)'
                    : 'UTXO PEELING CHAIN CARRY-FORWARD TRACE :: peel_0564 (4 Hops)'}
                </div>
                <div style={{ background: '#080808', border: '1px solid #1a1a1a', padding: '10px' }}>
                  {entry.content.candidateId === 'layer_1054' ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <div style={{ color: '#ef4444', fontWeight: 'bold' }}>
                        [FAN-OUT ORIGIN] <span className="cmd-tag" onClick={() => handleRunCommand('inspect 17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G')}>17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G</span> (LAYERING_FANOUT_SOURCE)
                        <span style={{ color: '#888888' }}> - Dispersed 2.5395 BTC across 14 smurf routes</span>
                      </div>
                      <div style={{ paddingLeft: '16px', color: '#888888', fontSize: '13px' }}>
                        ▼ Parallel Branch 1: 1Et4y3xsYY... ➔ 1snCZQN8XG... ➔ Reconvergence Sink (0.1800 BTC)
                      </div>
                      <div style={{ paddingLeft: '16px', color: '#888888', fontSize: '13px' }}>
                        ▼ Parallel Branch 2: 1SDQmJYVPc... ➔ 1QBMzLsqya... ➔ Reconvergence Sink (0.1900 BTC)
                      </div>
                      <div style={{ paddingLeft: '16px', color: '#888888', fontSize: '13px' }}>
                        ▼ Parallel Branch 3: 1d92F9SKdQ... ➔ 1RBv2NCXCT... ➔ Reconvergence Sink (0.2000 BTC)
                      </div>
                      <div style={{ paddingLeft: '16px', color: '#558866', fontSize: '13px' }}>
                        ... (11 additional parallel multi-hop branches executed within 34 hours) ...
                      </div>
                      <div style={{ color: '#ef4444', fontWeight: 'bold' }}>
                        [CONSOLIDATION SINK] <span className="cmd-tag" onClick={() => handleRunCommand('inspect 1JadLZMcaFX1JvRTkHmcAEZ4ygHm')}>1JadLZMcaFX1JvRTkHmcAEZ4ygHm</span> (LAYERING_CONSOLIDATION_SINK)
                        <span style={{ color: '#ef4444' }}> - 100% Reconvergence Ratio (Risk: 94/100)</span>
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <div style={{ color: '#ef4444' }}>
                        [HOP 1] <span className="cmd-tag" onClick={() => handleRunCommand('inspect 1PTqbgVoXSbuzQKrDGw2M2tchx')}>1PTqbgVoXSbuzQKrDGw2M2tchx</span> (PRIMARY_SUSPECT_PEEL_ORIGIN)
                        <span style={{ color: '#ef4444' }}> - Initial UTXO: 1.4809 BTC (Risk: 96/100)</span>
                      </div>
                      <div style={{ paddingLeft: '16px', color: '#888888', fontSize: '13px' }}>
                        ▼ Transferred 1.4809 BTC | Peeled: 0.0626 BTC | TX: 305493508 | Delay: 2.1h
                      </div>
                      <div style={{ color: '#f59e0b' }}>
                        [HOP 2] <span className="cmd-tag" onClick={() => handleRunCommand('inspect 1DnWHZtdtCP57xCqjbuBxkHXHqU')}>1DnWHZtdtCP57xCqjbuBxkHXHqU</span> (PEEL_HOP_1_RELAY)
                        <span style={{ color: '#f59e0b' }}> - Carry-Forward Balance: 1.4376 BTC (Risk: 91/100)</span>
                      </div>
                      <div style={{ paddingLeft: '16px', color: '#888888', fontSize: '13px' }}>
                        ▼ Transferred 1.4376 BTC | Peeled: 0.0430 BTC | TX: 616642538 | Delay: 2.7h
                      </div>
                      <div style={{ color: '#f59e0b' }}>
                        [HOP 3] <span className="cmd-tag" onClick={() => handleRunCommand('inspect 1wMdNuDqsBFmncgNNpa3eAxGXi4L')}>1wMdNuDqsBFmncgNNpa3eAxGXi4L</span> (PEEL_HOP_2_RELAY)
                        <span style={{ color: '#f59e0b' }}> - Carry-Forward Balance: 1.2576 BTC (Risk: 89/100)</span>
                      </div>
                      <div style={{ paddingLeft: '16px', color: '#888888', fontSize: '13px' }}>
                        ▼ Transferred 1.2576 BTC | Peeled: 0.1796 BTC | TX: 922456847 | Delay: 5.8h
                      </div>
                      <div style={{ color: '#ef4444' }}>
                        [HOP 4] <span className="cmd-tag" onClick={() => handleRunCommand('inspect 1s6D1TaSbKqeTG5YMhWWRJ85Ve8s7Y')}>1s6D1TaSbKqeTG5YMhWWRJ85Ve8s7Y</span> (UNLICENSED_OTC_EXIT_CORRIDOR)
                        <span style={{ color: '#ef4444' }}> - Terminal Cash-Out Desk: 1.1685 BTC Exit (Risk: 85/100)</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {entry.type === 'LOGS' && (
              <div className="output-block" style={{ color: '#dddddd' }}>
                <div style={{ color: '#00ff66', fontWeight: 600, marginBottom: '6px' }}>
                  KERNEL INTERCEPT STREAM (/var/log/bitkaun_v6.log)
                </div>
                <div style={{ background: '#080808', border: '1px solid #1a1a1a', padding: '10px', maxHeight: '300px', overflowY: 'auto', fontSize: '13px' }}>
                  {logs.map(log => (
                    <div key={log.id} style={{ display: 'flex', gap: '8px', marginBottom: '3px' }}>
                      <span style={{ color: '#555555' }}>{log.uptime}</span>
                      <span style={{ color: log.level === 'CRIT' ? '#ef4444' : log.level === 'WARN' ? '#f59e0b' : '#38ef7d' }}>
                        [{log.level}]
                      </span>
                      <span style={{ color: '#ffffff' }}>{log.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {entry.type === 'STATUS' && (
              <div className="output-block" style={{ color: '#dddddd' }}>
                <div style={{ color: '#00ff66', fontWeight: 600, marginBottom: '4px' }}>
                  BITKAUN GRAPH &amp; ML TELEMETRY DIAGNOSTICS
                </div>
                <div style={{ color: '#888888', fontSize: '14px', lineHeight: 1.5 }}>
                  • Dataset Version: Frozen V6.0 (Zero Split Contamination / No Address Leakage)<br />
                  • Total Heterogeneous Graph Nodes: {GRAPH_METADATA.total_nodes?.toLocaleString() || '459,975'} (Wallet: 346k | Tx: 96k | IP: 17k)<br />
                  • Total Multi-Directed Edges: {GRAPH_METADATA.total_edges?.toLocaleString() || '527,143'} (SENT, RECEIVED, BROADCAST)<br />
                  • Detected Candidate Structures: {GRAPH_METADATA.total_candidates?.toLocaleString() || '3,531'} (Peeling: 670, Layering: 1,778, Mixing: 1,083)<br />
                  • ML Stage 1 Classifier: XGBoost Binary (AUC ~0.999, Shallow-Tree BAcc 0.80)<br />
                  • ML Stage 2 Classifier: Multi-Class Typology (Macro-F1: 1.000 across 4 typologies)<br />
                  • Offline Compliance: 100% AIR-GAPPED VERIFIED (Zero external network telemetry)
                </div>
              </div>
            )}

            {entry.type === 'ERROR' && (
              <div className="output-block output-error">
                {entry.content.message}
              </div>
            )}

            {entry.type === 'SUCCESS' && (
              <div className="output-block output-success">
                {entry.content.message}
              </div>
            )}
>>>>>>> origin/graph
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
