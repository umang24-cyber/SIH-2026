import React, { useState, useEffect, useRef } from 'react';
import { ForensicNode, ForensicLink, KernelLogEntry } from '../types/terminal';
import { COMMAND_REGISTRY, MOCK_HEX_DUMPS } from '../data/mockForensicData';
import { GraphView3D } from './views/GraphView3D';
import { sound } from '../audio/soundEngine';
import { ForensicDashboard } from './dashboard/ForensicDashboard';

export interface TerminalEntry {
  id: string;
  command?: string;
  type: 'BANNER' | 'TEXT' | 'ERROR' | 'SUCCESS' | 'HELP' | 'INSPECT' | 'TRACE' | 'LOGS' | 'GRAPH' | 'STATUS';
  content?: any;
}

interface CliOutputRendererProps {
  entry: TerminalEntry;
  onRunCommand: (cmd: string) => void;
  nodes?: ForensicNode[];
  links?: ForensicLink[];
  logs?: KernelLogEntry[];
  onScrollRequested: () => void;
  onCloseEntry?: (id: string) => void;
}

export const CliOutputRenderer: React.FC<CliOutputRendererProps> = ({
  entry,
  onRunCommand,
  nodes = [],
  links = [],
  logs = [],
  onScrollRequested,
  onCloseEntry
}) => {
  const [revealedCount, setRevealedCount] = useState<number>(0);
  const [isFinished, setIsFinished] = useState<boolean>(false);
  const soundTickRef = useRef<number>(0);

  // Calculate total items to reveal
  let totalSteps = 1;
  if (entry.type === 'HELP') {
    totalSteps = COMMAND_REGISTRY.length + 1;
  } else if (entry.type === 'STATUS') {
    totalSteps = 6;
  } else if (entry.type === 'LOGS') {
    totalSteps = Math.min(logs.length, 12) + 1;
  } else if (entry.type === 'TRACE') {
    totalSteps = 8;
  } else if (entry.type === 'INSPECT') {
    const hexLines = MOCK_HEX_DUMPS[entry.content?.node?.id] || [
      '00000000  7f 45 4c 46 02 01 01 00  00 00 00 00 00 00 00 00  |.ELF............|',
      '00000010  03 00 3e 00 01 00 00 00  a0 14 00 00 00 00 00 00  |..>.............|',
      '00000020  40 00 00 00 00 00 00 00  78 3b 00 00 00 00 00 00  |@.......x;......|'
    ];
    totalSteps = 4 + hexLines.length;
  } else if (entry.type === 'ERROR' || entry.type === 'SUCCESS' || entry.type === 'TEXT') {
    const msg = entry.content?.message || '';
    totalSteps = Math.max(msg.length, 1);
  } else if (entry.type === 'GRAPH') {
    totalSteps = 3;
  }

  useEffect(() => {
    if (isFinished) return;

    // Initial scroll request so user's viewport is locked to output head immediately
    onScrollRequested();

    // 150ms buffer delay so user clearly sees the command prompt before lines start typing
    const startDelay = setTimeout(() => {
      // 1. Single-line character typewriter for errors/notices/text
      if (entry.type === 'ERROR' || entry.type === 'SUCCESS' || entry.type === 'TEXT') {
        const charInterval = 22; // 22ms per char
        const timer = setInterval(() => {
          setRevealedCount(prev => {
            const next = prev + 1;
            soundTickRef.current++;
            if (soundTickRef.current % 2 === 0) {
              sound.playKeyClick();
            }
            onScrollRequested();
            if (next >= totalSteps) {
              clearInterval(timer);
              setIsFinished(true);
              return totalSteps;
            }
            return next;
          });
        }, charInterval);
        return () => clearInterval(timer);
      }

      // 2. Line-by-line typewriter stream for tables/dossier/logs/trace (75ms per line)
      const lineInterval = entry.type === 'GRAPH' ? 140 : 75;
      const timer = setInterval(() => {
        setRevealedCount(prev => {
          const next = prev + 1;
          sound.playKeyClick();
          onScrollRequested();
          if (next >= totalSteps) {
            clearInterval(timer);
            setIsFinished(true);
            return totalSteps;
          }
          return next;
        });
      }, lineInterval);

      return () => clearInterval(timer);
    }, 150);

    return () => clearTimeout(startDelay);
  }, [entry.type, totalSteps, isFinished, onScrollRequested]);

  // Click output to instantly complete animation
  const handleFastForward = () => {
    setRevealedCount(totalSteps);
    setIsFinished(true);
    onScrollRequested();
  };

  return (
    <div onClick={handleFastForward} style={{ cursor: isFinished ? 'inherit' : 'pointer' }}>
      {/* 1. HELP TABLE STREAM */}
      {entry.type === 'HELP' && (
        <div className="output-block" style={{ color: 'var(--fg-text)' }}>
          <div style={{ color: 'var(--fg-primary)', fontWeight: 700, marginBottom: '6px' }}>
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
              {COMMAND_REGISTRY.slice(0, revealedCount).map((cmd) => (
                <tr key={cmd.name} className="cli-line-fade">
                  <td style={{ color: 'var(--fg-highlight)', fontWeight: 700 }}>
                    <span className="cmd-tag" onClick={() => onRunCommand(cmd.name)}>
                      {cmd.name}
                    </span>
                  </td>
                  <td style={{ color: 'var(--fg-muted)' }}>{cmd.aliases.join(', ')}</td>
                  <td>
                    <div>{cmd.summary}</div>
                    <div style={{ color: 'var(--fg-primary)', fontSize: '15px', marginTop: '2px' }}>
                      Try:&nbsp;
                      <span className="cmd-tag" onClick={() => onRunCommand(cmd.examples[0])}>
                        {cmd.examples[0]}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!isFinished && (
            <div style={{ display: 'inline-flex', alignItems: 'center', marginTop: '4px' }}>
              <span style={{ color: 'var(--fg-muted)', fontSize: '14px', marginRight: '6px' }}>[streaming stdout...]</span>
              <span className="cli-cursor" />
            </div>
          )}
        </div>
      )}

      {/* 2. FORENSIC GRAPH HUD WORKSPACE (Embedded in CLI Stream) */}
      {entry.type === 'GRAPH' && (
        <div className="output-block" style={{ width: '100%' }}>
          <ForensicDashboard
            onClose={() => {
              if (onCloseEntry) {
                onCloseEntry(entry.id);
              }
            }}
          />
        </div>
      )}

      {/* 3. INSPECT DOSSIER STREAM */}
      {entry.type === 'INSPECT' && (
        <div className="output-block" style={{ color: 'var(--fg-text)' }}>
          {(() => {
            const node = entry.content.node as ForensicNode;
            const hexLines = MOCK_HEX_DUMPS[node.id] || [
              '00000000  7f 45 4c 46 02 01 01 00  00 00 00 00 00 00 00 00  |.ELF............|',
              '00000010  03 00 3e 00 01 00 00 00  a0 14 00 00 00 00 00 00  |..>.............|',
              '00000020  40 00 00 00 00 00 00 00  78 3b 00 00 00 00 00 00  |@.......x;......|'
            ];
            return (
              <div>
                <div style={{ color: 'var(--fg-primary)', fontWeight: 700, marginBottom: '6px' }}>
                  ENTITY DOSSIER: {node.id} ({node.label})
                </div>

                {revealedCount >= 1 && (
                  <table className="cli-table cli-line-fade">
                    <tbody>
                      <tr>
                        <td style={{ color: 'var(--fg-muted)', width: '20%' }}>Type / Role</td>
                        <td style={{ color: 'var(--fg-white)' }}>{node.type}</td>
                        <td style={{ color: 'var(--fg-muted)', width: '20%' }}>Risk Score</td>
                        <td style={{ color: node.riskScore >= 80 ? 'var(--fg-danger)' : 'var(--fg-primary)', fontWeight: 'bold' }}>
                          {node.riskScore}/100 {node.riskScore >= 80 ? '(CRITICAL)' : '(NORMAL)'}
                        </td>
                      </tr>
                      {revealedCount >= 2 && (
                        <tr className="cli-line-fade">
                          <td style={{ color: 'var(--fg-muted)' }}>Cluster Affiliation</td>
                          <td style={{ color: '#38bdf8' }}>{node.clusterId}</td>
                          <td style={{ color: 'var(--fg-muted)' }}>Balance</td>
                          <td style={{ color: 'var(--fg-primary)' }}>{node.balanceEth} ETH ({node.txCount} txs)</td>
                        </tr>
                      )}
                      {revealedCount >= 3 && (
                        <tr className="cli-line-fade">
                          <td style={{ color: 'var(--fg-muted)' }}>AML Flags</td>
                          <td colSpan={3} style={{ color: 'var(--fg-warn)' }}>
                            {node.flags.join(' | ')}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                )}

                {revealedCount >= 4 && (
                  <div className="cli-line-fade" style={{ marginTop: '6px' }}>
                    <div style={{ fontSize: '15px', color: 'var(--fg-muted)', marginBottom: '2px' }}>
                      Bytecode Memory Hexdump:
                    </div>
                    <pre style={{ color: 'var(--fg-primary)', fontSize: '15px', background: 'var(--bg-card)', padding: '8px', border: '1px solid var(--border-dim)' }}>
                      {hexLines.slice(0, Math.max(0, revealedCount - 3)).join('\n')}
                    </pre>
                  </div>
                )}
                {!isFinished && <span className="cli-cursor" style={{ marginLeft: '4px' }} />}
              </div>
            );
          })()}
        </div>
      )}

      {/* 4. MULTI-HOP TRACE STREAM */}
      {entry.type === 'TRACE' && (
        <div className="output-block" style={{ color: 'var(--fg-text)' }}>
          <div style={{ color: 'var(--fg-primary)', fontWeight: 700, marginBottom: '6px' }}>
            FUND ROUTE TRACE: {entry.content.src} ===&gt; {entry.content.dst}
          </div>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-dim)', padding: '12px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {revealedCount >= 1 && (
                <div className="cli-line-fade" style={{ color: 'var(--fg-primary)' }}>
                  [HOP 1] <span className="cmd-tag" onClick={() => onRunCommand('inspect 0x5C8821FF')}>0x5C8821FF</span> (VICTIM_TREASURY_VAULT)
                  <span style={{ color: 'var(--fg-muted)' }}> - Source Drain</span>
                </div>
              )}
              {revealedCount >= 2 && (
                <div className="cli-line-fade" style={{ paddingLeft: '16px', color: 'var(--fg-muted)', fontSize: '15px' }}>
                  ▼ Sent 2500.0 ETH | TX: 0x9a8f3b20c1d4... | Suspicious Peeling
                </div>
              )}
              {revealedCount >= 3 && (
                <div className="cli-line-fade" style={{ color: 'var(--fg-danger)' }}>
                  [HOP 2] <span className="cmd-tag" onClick={() => onRunCommand('inspect 0x71C84A9E')}>0x71C84A9E</span> (PRIMARY_SUSPECT_01)
                  <span style={{ color: 'var(--fg-danger)' }}> - Exploiter / Peeling Chain (Risk: 94/100)</span>
                </div>
              )}
              {revealedCount >= 4 && (
                <div className="cli-line-fade" style={{ paddingLeft: '16px', color: 'var(--fg-muted)', fontSize: '15px' }}>
                  ▼ Sent 1080.0 ETH | TX: 0x1b2c3d4e5f6a... | Mixer Inflow
                </div>
              )}
              {revealedCount >= 5 && (
                <div className="cli-line-fade" style={{ color: 'var(--fg-warn)' }}>
                  [HOP 3] <span className="cmd-tag" onClick={() => onRunCommand('inspect 0x44B12D03')}>0x44B12D03</span> (MIXER_HOP_POOL_01)
                  <span style={{ color: 'var(--fg-warn)' }}> - Tornado Relay Tranche (Risk: 88/100)</span>
                </div>
              )}
              {revealedCount >= 6 && (
                <div className="cli-line-fade" style={{ paddingLeft: '16px', color: 'var(--fg-muted)', fontSize: '15px' }}>
                  ▼ Sent 320.0 ETH | TX: 0x5e6f7a8b9c0d... | Fiat Exit Corridor
                </div>
              )}
              {revealedCount >= 7 && (
                <div className="cli-line-fade" style={{ color: 'var(--fg-danger)' }}>
                  [HOP 4] <span className="cmd-tag" onClick={() => onRunCommand('inspect 0xEE3388A1')}>0xEE3388A1</span> (UNLICENSED_OTC_DESK)
                  <span style={{ color: 'var(--fg-danger)' }}> - Destination Cashout Ring (Risk: 82/100)</span>
                </div>
              )}
            </div>
          </div>
          {!isFinished && <span className="cli-cursor" style={{ marginLeft: '4px' }} />}
        </div>
      )}

      {/* 5. KERNEL LOGS STREAM */}
      {entry.type === 'LOGS' && (
        <div className="output-block" style={{ color: 'var(--fg-text)' }}>
          <div style={{ color: 'var(--fg-primary)', fontWeight: 700, marginBottom: '6px' }}>
            KERNEL INTERCEPT STREAM (/var/log/bitkaun.log)
          </div>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-dim)', padding: '10px', maxHeight: '360px', overflowY: 'auto', fontSize: '15px' }}>
            {logs.slice(0, revealedCount).map((log) => (
              <div key={log.id} className="cli-line-fade" style={{ display: 'flex', gap: '8px', marginBottom: '3px' }}>
                <span style={{ color: 'var(--fg-muted)' }}>{log.uptime}</span>
                <span style={{ color: log.level === 'CRIT' ? 'var(--fg-danger)' : log.level === 'WARN' ? 'var(--fg-warn)' : 'var(--fg-primary)' }}>
                  [{log.level}]
                </span>
                <span style={{ color: 'var(--fg-white)' }}>{log.message}</span>
              </div>
            ))}
          </div>
          {!isFinished && <span className="cli-cursor" style={{ marginLeft: '4px' }} />}
        </div>
      )}

      {/* 6. STATUS STREAM */}
      {entry.type === 'STATUS' && (
        <div className="output-block" style={{ color: 'var(--fg-text)' }}>
          <div style={{ color: 'var(--fg-primary)', fontWeight: 700, marginBottom: '4px' }}>
            BITKAUN SYSTEM DIAGNOSTICS
          </div>
          <div style={{ color: 'var(--fg-muted)', fontSize: '16px' }}>
            {revealedCount >= 1 && <div className="cli-line-fade">• OS Kernel: BitKaun-Linux 6.9.4-forensic x86_64</div>}
            {revealedCount >= 2 && <div className="cli-line-fade">• Active Node Entities: {nodes.length} mapped</div>}
            {revealedCount >= 3 && <div className="cli-line-fade">• Directed Edge Links: {links.length} indexed</div>}
            {revealedCount >= 4 && <div className="cli-line-fade">• Active Session: root@bitkaun-terminal (TTY1)</div>}
            {revealedCount >= 5 && <div className="cli-line-fade">• Anomaly Detection Pipeline: ONLINE (100% heuristic coverage)</div>}
          </div>
          {!isFinished && <span className="cli-cursor" style={{ marginLeft: '4px' }} />}
        </div>
      )}

      {/* 7. ERROR MESSAGE TYPEWRITER */}
      {entry.type === 'ERROR' && (
        <div className="output-block output-error">
          {entry.content?.message ? entry.content.message.slice(0, revealedCount) : ''}
          {!isFinished && <span className="cli-cursor" />}
        </div>
      )}

      {/* 8. SUCCESS MESSAGE TYPEWRITER */}
      {entry.type === 'SUCCESS' && (
        <div className="output-block output-success">
          {entry.content?.message ? entry.content.message.slice(0, revealedCount) : ''}
          {!isFinished && <span className="cli-cursor" />}
        </div>
      )}

      {/* 9. RAW TEXT TYPEWRITER */}
      {entry.type === 'TEXT' && (
        <div className="output-block" style={{ color: 'var(--fg-white)' }}>
          {entry.content?.message ? entry.content.message.slice(0, revealedCount) : ''}
          {!isFinished && <span className="cli-cursor" />}
        </div>
      )}
    </div>
  );
};
