import React from 'react';
import { COMMAND_REGISTRY } from '../../data/mockForensicData';
import { CommandDescriptor } from '../../types/terminal';

interface HelpManualViewProps {
  filterCommand?: string | null;
  onRunCommand: (cmd: string) => void;
}

export const HelpManualView: React.FC<HelpManualViewProps> = ({
  filterCommand,
  onRunCommand
}) => {
  const specificCmd = filterCommand
    ? COMMAND_REGISTRY.find(
        c =>
          c.name.toLowerCase() === filterCommand.toLowerCase() ||
          c.aliases.includes(filterCommand.toLowerCase())
      )
    : null;

  return (
    <div style={{ maxWidth: '1050px', margin: '0 auto', fontSize: '16px' }}>
      <div className="man-header">
        <strong>HOLMES-MAN(1)</strong> :: FORENSIC SYSCALL MANUAL PAGE :: <strong>HOLMES-MAN(1)</strong>
      </div>

      {specificCmd ? (
        // Specific command detail
        <div>
          <div className="man-section-title">NAME</div>
          <p style={{ paddingLeft: '16px' }}>
            <strong>{specificCmd.name}</strong> - {specificCmd.summary}
          </p>

          <div className="man-section-title">SYNOPSIS</div>
          <div style={{ paddingLeft: '16px', color: '#33ff88' }}>
            <code>{specificCmd.usage}</code>
          </div>

          <div className="man-section-title">ALIASES</div>
          <p style={{ paddingLeft: '16px' }}>
            {specificCmd.aliases.map(a => (
              <span key={a} className="cmd-clickable" onClick={() => onRunCommand(a)} style={{ marginRight: '10px' }}>
                {a}
              </span>
            ))}
          </p>

          <div className="man-section-title">DESCRIPTION</div>
          <p style={{ paddingLeft: '16px', color: '#00ff66', lineHeight: 1.4 }}>
            {specificCmd.description}
          </p>

          <div className="man-section-title">EXAMPLES & INVOCATION</div>
          <div style={{ paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {specificCmd.examples.map(ex => (
              <div key={ex}>
                <code>&gt; </code>
                <span className="cmd-clickable" onClick={() => onRunCommand(ex)}>
                  {ex}
                </span>
              </div>
            ))}
          </div>

          <div style={{ marginTop: '24px', borderTop: '1px solid #007a33', paddingTop: '8px' }}>
            <span className="cmd-clickable" onClick={() => onRunCommand('help')}>
              &lt;&lt; Return to Full System Manual
            </span>
          </div>
        </div>
      ) : (
        // Full command index & tutorial
        <div>
          <div className="man-section-title">NAME</div>
          <p style={{ paddingLeft: '16px' }}>
            <strong>bitkaun-terminal</strong> - Interactive 3D graph cryptocurrency & blockchain forensic console (V8 Air-Gapped Engine).
          </p>

          <div className="man-section-title">FORENSIC INVESTIGATION WORKFLOW (HOW TO USE)</div>
          <div style={{ paddingLeft: '16px', borderLeft: '2px solid #00ff66', marginLeft: '8px', paddingBottom: '4px' }}>
            <p style={{ marginBottom: '6px' }}>
              <strong>Step 1: Explore Scenarios & Graph Topology</strong> — Type <span className="cmd-clickable" onClick={() => onRunCommand('scenarios')}>scenarios</span> or <span className="cmd-clickable" onClick={() => onRunCommand('graph')}>graph</span> to mount the 3D Force-Directed Graph canvas.
            </p>
            <p style={{ marginBottom: '6px' }}>
              <strong>Step 2: Inspect Financial Flows & Entities</strong> — Type <span className="cmd-clickable" onClick={() => onRunCommand('inspect 881920041')}>inspect 881920041</span> or <span className="cmd-clickable" onClick={() => onRunCommand('flow 881920041')}>flow 881920041</span> to audit UTXO amounts, fees, and CIOH clusters.
            </p>
            <p style={{ marginBottom: '6px' }}>
              <strong>Step 3: Propagate Taint & Multi-Hop Trace</strong> — Type <span className="cmd-clickable" onClick={() => onRunCommand('taint 18hvz1KnqUjLRr3KHifSbMDi6m')}>taint 18hvz1KnqUjLRr3KHifSbMDi6m</span> to calculate dirty coin decay across hops.
            </p>
            <p style={{ marginBottom: '6px' }}>
              <strong>Step 4: Audit Syndicates & Anomalies</strong> — Type <span className="cmd-clickable" onClick={() => onRunCommand('communities peeling_chain_04651')}>communities peeling_chain_04651</span> and <span className="cmd-clickable" onClick={() => onRunCommand('anomaly peeling_chain_04651')}>anomaly peeling_chain_04651</span>.
            </p>
            <p style={{ marginBottom: '6px' }}>
              <strong>Step 5: Review ML Alerts & Benchmark</strong> — Type <span className="cmd-clickable" onClick={() => onRunCommand('alerts')}>alerts</span> or <span className="cmd-clickable" onClick={() => onRunCommand('benchmark')}>benchmark</span> for detection accuracy and SHAP explainability.
            </p>
          </div>

          <div className="man-section-title">AVAILABLE SYSCALLS & COMMAND REGISTRY</div>
          <div style={{ paddingLeft: '16px' }}>
            <table className="hex-table" style={{ marginTop: '8px' }}>
              <thead>
                <tr>
                  <th style={{ width: '22%' }}>COMMAND & USAGE</th>
                  <th style={{ width: '18%' }}>ALIASES</th>
                  <th style={{ width: '60%' }}>DESCRIPTION & EXAMPLES</th>
                </tr>
              </thead>
              <tbody>
                {COMMAND_REGISTRY.map((cmd: CommandDescriptor) => (
                  <tr key={cmd.name}>
                    <td>
                      <strong style={{ color: '#33ff88' }}>{cmd.name}</strong>
                      <div style={{ fontSize: '13px', color: '#007a33' }}>{cmd.usage}</div>
                    </td>
                    <td>
                      {cmd.aliases.map(a => (
                        <span key={a} className="cmd-clickable" onClick={() => onRunCommand(a)} style={{ marginRight: '6px', display: 'inline-block' }}>
                          {a}
                        </span>
                      ))}
                    </td>
                    <td>
                      <div>{cmd.summary}</div>
                      <div style={{ marginTop: '4px', fontSize: '13px', color: '#33ff88' }}>
                        <span>Try: </span>
                        {cmd.examples.slice(0, 2).map((ex, idx) => (
                          <span key={ex}>
                            {idx > 0 && <span style={{ color: '#007a33' }}> | </span>}
                            <span className="cmd-clickable" onClick={() => onRunCommand(ex)}>
                              {ex}
                            </span>
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="man-section-title">TERMINAL KEYBOARD SHORTCUTS</div>
          <div style={{ paddingLeft: '16px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '8px' }}>
            <div style={{ border: '1px solid #004d20', padding: '6px' }}>
              <strong>[TAB]</strong> - Autocomplete command or entity address
            </div>
            <div style={{ border: '1px solid #004d20', padding: '6px' }}>
              <strong>[UP] / [DOWN]</strong> - Navigate command execution history
            </div>
            <div style={{ border: '1px solid #004d20', padding: '6px' }}>
              <strong>[Ctrl + L]</strong> - Clear terminal history buffer
            </div>
            <div style={{ border: '1px solid #004d20', padding: '6px' }}>
              <strong>[ESC]</strong> - Clear current prompt input
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
