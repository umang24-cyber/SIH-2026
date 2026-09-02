import React, { useState, useEffect, useRef } from 'react';
import { ForensicNode, ForensicLink, KernelLogEntry, CommandDescriptor } from './types/terminal';
import { INITIAL_NODES, INITIAL_LINKS, INITIAL_LOGS, COMMAND_REGISTRY, MOCK_HEX_DUMPS } from './data/mockForensicData';
import { GraphView3D } from './components/views/GraphView3D';
import { sound } from './audio/soundEngine';

interface TerminalEntry {
  id: string;
  command?: string;
  type: 'BANNER' | 'TEXT' | 'ERROR' | 'SUCCESS' | 'HELP' | 'INSPECT' | 'TRACE' | 'LOGS' | 'GRAPH' | 'STATUS';
  content?: any;
}

export function App() {
  const [nodes] = useState<ForensicNode[]>(INITIAL_NODES);
  const [links] = useState<ForensicLink[]>(INITIAL_LINKS);
  const [logs, setLogs] = useState<KernelLogEntry[]>(INITIAL_LOGS);

  const [inputVal, setInputVal] = useState<string>('');
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIdx, setHistoryIdx] = useState<number>(-1);
  const [entries, setEntries] = useState<TerminalEntry[]>([]);

  const inputRef = useRef<HTMLInputElement>(null);
  const scrollBottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new entries
  useEffect(() => {
    scrollBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
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

    const tokens = trimmed.split(/\s+/);
    const root = tokens[0].toLowerCase();
    const arg1 = tokens[1];
    const arg2 = tokens[2];

    sound.playKeyClick();

    switch (root) {
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
          const targetId = arg1 || '0x71C84A9E';
          const match = nodes.find(n => n.id.toLowerCase() === targetId.toLowerCase());
          if (match) {
            sound.playEnterSuccess();
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'INSPECT',
                content: { node: match }
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
                  message: `Entity not found: '${targetId}'. Known nodes: ${nodes.map(n => n.id).join(', ')}`
                }
              }
            ]);
          }
        }
        break;

      case 'trace':
      case 'tr':
      case 'path':
      case 'flow':
        {
          const src = arg1 || '0x5C8821FF';
          const dst = arg2 || '0xEE3388A1';
          sound.playEnterSuccess();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'TRACE',
              content: { src, dst }
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
      const allCmds = ['graph', 'inspect', 'trace', 'dmesg', 'help', 'status', 'clear', 'banner', 'sound'];
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
      <div className="terminal-body">
        {/* Permanent Welcome Header & Available Commands (Never Erased) */}
        <div className="output-block" style={{ borderBottom: '1px solid var(--border-mid)', paddingBottom: '14px', marginBottom: '8px' }}>
          <pre className="ansi-shadow-logo">{`██████╗ ██╗████████╗██╗  ██╗ █████╗ ██╗   ██╗███╗   ██╗██████╗ 
██╔══██╗██║╚══██╔══╝██║ ██╔╝██╔══██╗██║   ██║████╗  ██║╚════██╗
██████╔╝██║   ██║   █████╔╝ ███████║██║   ██║██╔██╗ ██║  ▄███╔╝
██╔══██╗██║   ██║   ██╔═██╗ ██╔══██║██║   ██║██║╚██╗██║  ▀▀══╝ 
██████╔╝██║   ██║   ██║  ██╗██║  ██║╚██████╔╝██║ ╚████║  ██╗   
╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝  ╚═╝   `}</pre>

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
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', marginBottom: '14px', color: 'var(--fg-text)' }}>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('graph')}>[graph]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('g')}>[g]</span>
              <span className="cmd-desc">- 3D interactive force graph of wallets &amp; transaction links</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('inspect 0x71C84A9E')}>[inspect &lt;id&gt;]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('cat 0x71C84A9E')}>[cat]</span>
              <span className="cmd-desc">- Inspect entity dossier, AML risk score &amp; bytecode hexdump</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('trace 0x5C8821FF 0xEE3388A1')}>[trace &lt;src&gt; &lt;dst&gt;]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('tr 0x5C8821FF 0xEE3388A1')}>[tr]</span>
              <span className="cmd-desc">- Trace multi-hop laundering flow between addresses</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('dmesg')}>[dmesg]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('logs')}>[logs]</span>
              <span className="cmd-desc">- Stream realtime kernel threat alerts &amp; mempool intercepts</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('status')}>[status]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('top')}>[top]</span>
              <span className="cmd-desc">- System diagnostics &amp; active cluster statistics</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('clear')}>[clear]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('cls')}>[cls]</span>
              <span className="cmd-desc">- Clear the terminal output (Shortcut: Ctrl+L)</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('help')}>[help]</span> or <span className="cmd-tag" onClick={() => handleRunCommand('man')}>[man]</span>
              <span className="cmd-desc">- Detailed command manual and usage examples</span>
            </div>
          </div>

          <div style={{ color: 'var(--fg-primary)', fontWeight: 600, marginBottom: '6px' }}>
            Quick Queries:
          </div>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <span className="cmd-tag" onClick={() => handleRunCommand('inspect 0x71C84A9E')}>
              [inspect 0x71C84A9E]
            </span>
            <span className="cmd-tag" onClick={() => handleRunCommand('inspect 0x77DD9900')}>
              [inspect 0x77DD9900]
            </span>
            <span className="cmd-tag" onClick={() => handleRunCommand('trace 0x5C8821FF 0xEE3388A1')}>
              [trace 0x5C8821FF 0xEE3388A1]
            </span>
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

            {/* Entry Content Rendering */}

            {entry.type === 'HELP' && (
              <div className="output-block" style={{ color: 'var(--fg-text)' }}>
                <div style={{ color: 'var(--fg-primary)', fontWeight: 600, marginBottom: '6px' }}>
                  BITKAUN MANUAL (1) - FORENSIC COMMAND REGISTRY
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
                  <span>&gt; 3D Force-Directed Graph mounted ({nodes.length} nodes, {links.length} edges)</span>
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
                    '00000000  7f 45 4c 46 02 01 01 00  00 00 00 00 00 00 00 00  |.ELF............|',
                    '00000010  03 00 3e 00 01 00 00 00  a0 14 00 00 00 00 00 00  |..>.............|',
                    '00000020  40 00 00 00 00 00 00 00  78 3b 00 00 00 00 00 00  |@.......x;......|'
                  ];
                  return (
                    <div>
                      <div style={{ color: '#00ff66', fontWeight: 600, marginBottom: '6px' }}>
                        ENTITY DOSSIER: {node.id} ({node.label})
                      </div>
                      <table className="cli-table">
                        <tbody>
                          <tr>
                            <td style={{ color: '#888888', width: '20%' }}>Type / Role</td>
                            <td style={{ color: '#ffffff' }}>{node.type}</td>
                            <td style={{ color: '#888888', width: '20%' }}>Risk Score</td>
                            <td style={{ color: node.riskScore >= 80 ? '#ef4444' : '#22c55e', fontWeight: 'bold' }}>
                              {node.riskScore}/100 {node.riskScore >= 80 ? '(CRITICAL)' : '(NORMAL)'}
                            </td>
                          </tr>
                          <tr>
                            <td style={{ color: '#888888' }}>Cluster Affiliation</td>
                            <td style={{ color: '#38bdf8' }}>{node.clusterId}</td>
                            <td style={{ color: '#888888' }}>Balance</td>
                            <td style={{ color: '#38ef7d' }}>{node.balanceEth} ETH ({node.txCount} txs)</td>
                          </tr>
                          <tr>
                            <td style={{ color: '#888888' }}>AML Flags</td>
                            <td colSpan={3} style={{ color: '#f59e0b' }}>
                              {node.flags.join(' | ')}
                            </td>
                          </tr>
                        </tbody>
                      </table>

                      <div style={{ fontSize: '13px', color: '#888888', marginTop: '6px', marginBottom: '2px' }}>
                        Bytecode Memory Hexdump:
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
                  FUND ROUTE TRACE: {entry.content.src} ===&gt; {entry.content.dst}
                </div>
                <div style={{ background: '#080808', border: '1px solid #1a1a1a', padding: '10px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ color: '#38ef7d' }}>
                      [HOP 1] <span className="cmd-tag" onClick={() => handleRunCommand('inspect 0x5C8821FF')}>0x5C8821FF</span> (VICTIM_TREASURY_VAULT)
                      <span style={{ color: '#888888' }}> - Source Drain</span>
                    </div>
                    <div style={{ paddingLeft: '16px', color: '#888888', fontSize: '13px' }}>
                      ▼ Sent 2500.0 ETH | TX: 0x9a8f3b20c1d4... | Suspicious Peeling
                    </div>
                    <div style={{ color: '#ef4444' }}>
                      [HOP 2] <span className="cmd-tag" onClick={() => handleRunCommand('inspect 0x71C84A9E')}>0x71C84A9E</span> (PRIMARY_SUSPECT_01)
                      <span style={{ color: '#ef4444' }}> - Exploiter / Peeling Chain (Risk: 94/100)</span>
                    </div>
                    <div style={{ paddingLeft: '16px', color: '#888888', fontSize: '13px' }}>
                      ▼ Sent 1080.0 ETH | TX: 0x1b2c3d4e5f6a... | Mixer Inflow
                    </div>
                    <div style={{ color: '#f59e0b' }}>
                      [HOP 3] <span className="cmd-tag" onClick={() => handleRunCommand('inspect 0x44B12D03')}>0x44B12D03</span> (MIXER_HOP_POOL_01)
                      <span style={{ color: '#f59e0b' }}> - Tornado Relay Tranche (Risk: 88/100)</span>
                    </div>
                    <div style={{ paddingLeft: '16px', color: '#888888', fontSize: '13px' }}>
                      ▼ Sent 320.0 ETH | TX: 0x5e6f7a8b9c0d... | Fiat Exit Corridor
                    </div>
                    <div style={{ color: '#ef4444' }}>
                      [HOP 4] <span className="cmd-tag" onClick={() => handleRunCommand('inspect 0xEE3388A1')}>0xEE3388A1</span> (UNLICENSED_OTC_DESK)
                      <span style={{ color: '#ef4444' }}> - Destination Cashout Ring (Risk: 82/100)</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {entry.type === 'LOGS' && (
              <div className="output-block" style={{ color: '#dddddd' }}>
                <div style={{ color: '#00ff66', fontWeight: 600, marginBottom: '6px' }}>
                  KERNEL INTERCEPT STREAM (/var/log/bitkaun.log)
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
                  BITKAUN SYSTEM DIAGNOSTICS
                </div>
                <div style={{ color: '#888888', fontSize: '14px' }}>
                  • OS Kernel: BitKaun-Linux 6.9.4-forensic x86_64<br />
                  • Active Node Entities: {nodes.length} mapped<br />
                  • Directed Edge Links: {links.length} indexed<br />
                  • Active Session: root@bitkaun-terminal (TTY1)<br />
                  • Anomaly Detection Pipeline: ONLINE (100% heuristic coverage)
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
