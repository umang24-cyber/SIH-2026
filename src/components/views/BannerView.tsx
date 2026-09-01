import React from 'react';

interface BannerViewProps {
  onRunCommand: (cmd: string) => void;
}

export const BannerView: React.FC<BannerViewProps> = ({ onRunCommand }) => {
  return (
    <div style={{ maxWidth: '1150px', margin: '0 auto' }}>
      {/* Grand BitKaun? ASCII Logo Header */}
      <div style={{ border: '1px solid #00ff66', padding: '14px 16px', marginBottom: '14px', background: '#000d04', textAlign: 'center' }}>
        <pre className="ascii-art" style={{ fontSize: '15px', fontWeight: 'bold', color: '#33ff88', overflowX: 'auto', display: 'inline-block', textAlign: 'left' }}>
{`    ____  _ __  __ __                ___ 
   / __ )(_) /_/ //_/___ ___  ______/__ \\
  / __  / / __/ ,< / __ \`/ / / / __ \\/ _/
 / /_/ / / /_/ /| / /_/ / /_/ / / / /_/  
/_____/_/\\__/_/ |_\\__,_/\\__,_/_/ /_(_)   `}
        </pre>
        <div style={{ marginTop: '6px', fontSize: '15px', color: '#00ff66', letterSpacing: '1px' }}>
          <strong>[ BIT-KAUN? (बिट-कौन?) ]</strong> :: ON-CHAIN TRANSACTION FORENSICS &amp; ANOMALY SURVEILLANCE
        </div>
        <div style={{ fontSize: '13px', color: '#00aa44', marginTop: '2px' }}>
          <em>"Kaun?" (Who?) — Unmasking anomalous crypto flows, mixer hops, and illicit wallet syndicates.</em>
        </div>
      </div>

      {/* Sherlock Holmes 3 Themed Forensic ASCII Artifacts */}
      <div style={{ border: '1px solid #007a33', padding: '12px', marginBottom: '16px', background: '#000802' }}>
        <pre className="ascii-art" style={{ fontSize: '12px', overflowX: 'auto' }}>
{`      [ EVIDENCE SCANNER ]                        [ NOIR FEDORA ]                       [ BENT FILIGREE PIPE ]
  ⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀   ⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀⣀⣀⣀⠀⠀⠀⠀⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣤⣤⣤⣤⣀⣀⣀⣀
  ⠀⠀⠀⠀⢀⣴⠾⠛⢉⣉⣉⣉⡉⠛⠷⣦⣄⠀⠀   ⠀⠀⠀⢀⣠⣴⠾⠛⠛⠉⠉⠉⠉⠙⠛⠛⠿⣶⣤⣄   ⠀⠀⠀⠀⠀⠀⢀⣴⡿⠛⠉⠉⠉⠉⠉⠛⠿⢿⣿
  ⠀⠀⢀⣴⠋⣠⣴⣿⣿⣿⣿⣿⡿⣿⣶⣌⠹⣷⡀   ⠀⢰⣿⠃⠀⣰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣆⠀⣿   ⠀⠀⠀⠀⠀⠀⣾⡏⠀⢀⣴⠾⠿⠿⠷⣦⡀⠀⢹
  ⠀⠀⣼⠁⣴⣿⣿⣿⣿⣿⣿⣿⣿⣆⠉⠻⣧⠘⣷   ⠀⣿⡇⠀⠀⠹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠏⠀⢸⣿   ⠀⠀⠀⠀⠀⠀⣿⡇⠀⢸⣯⡀⠀⠀⢀⣼⡇⠀⢸
  ⠀⢰⡇⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀⠀⠈⠀⢸   ⠀⢹⣷⡀⠀⠀⠈⠛⠿⢿⣿⣿⣿⣿⣿⠿⠛⠀⣾⡏   ⠀⠀⠀⠀⠀⠀⣿⡇⠀⠈⠛⠿⣶⣾⠿⠛⠁⠀⣸
  ⠀⢸⡇⢸⣿⠛⣿⣿⣿⣿⣿⣿⡿⠃⠀⠀⠀⠀⢸   ⠀⠀⢀⣀⣀⣹⣿⣶⣤⣤⣀⣀⣀⣀⣀⣀⣤⣶⣿⣋   ⠀⠀⠀⠀⠀⠀⢿⣇⠀⢰⣶⣤⣀⣀⣤⣶⡆⠀⣿
  ⠀⠈⣷⠀⢿⡆⠈⠛⠻⠟⠛⠉⠀⠀⠀⠀⠀⠀⣾   ⢀⣠⣴⣶⠿⠿⠛⠛⠛⠉⠉⠉⠉⠛⠛⠛⠉⠉⠉⠛   ⠀⠀⠀⠀⠀⠀⠈⢿⣦⡀⠈⠉⠛⠛⠉⠉⠀⣼⣿
  ⠀⠀⠸⣧⡀⠻⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⠃   ⣠⣾⠟⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠙⠿⣶⣤⣤⣤⣤⣴⣾⠿⠟
  ⠀⠀⠀⢼⠿⣦⣄⠀⠀⠀⠀⠀⠀⠀⣀⣴⠟⠁⠀   ⠻⣷⣶⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠉⠉⠉⠀⠀⠀
  ⣠⣾⣿⣦⠀⠀⠈⠉⠛⠓⠲⠶⠖⠚⠋⠉⠀⠀⠀   ⠀⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
  ⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀`}
        </pre>
      </div>

      {/* System Intro Box */}
      <div style={{ border: '1px solid #00ff66', padding: '14px', background: '#001406', marginBottom: '16px' }}>
        <h2 style={{ fontSize: '17px', color: '#33ff88', marginBottom: '6px', textTransform: 'uppercase' }}>
          &gt;&gt;&gt; BITKAUN? ANOMALY RADAR READY :: TTY1 SHELL ENVIRONMENT
        </h2>
        <p style={{ color: '#00ff66', marginBottom: '8px', fontSize: '15px' }}>
          Welcome, Investigator. <strong>BitKaun?</strong> tracks anomalous multi-hop transactions, identifies laundering mixers, and exposes illicit wallet clusters across EVM and UTXO networks.
        </p>
        <p style={{ color: '#33ff88', fontSize: '14px' }}>
          <strong>Interactive Navigation:</strong> This console is 100% CLI &amp; keyboard operated. Type commands in the prompt below or click any underlined syscall to switch buffers immediately.
        </p>
      </div>

      {/* Interactive Quick Start Matrix */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '12px', marginBottom: '16px' }}>
        <div style={{ border: '1px solid #007a33', padding: '10px', background: '#000802' }}>
          <h3 style={{ color: '#33ff88', marginBottom: '6px', fontSize: '16px' }}>[1] 3D ANOMALY TOPOLOGY GRAPH</h3>
          <p style={{ fontSize: '15px', color: '#00ff66', marginBottom: '6px' }}>
            Mount the real-time 3D Force-Directed Graph canvas to explore entity clusters, transaction links, and photon particle beams:
          </p>
          <div style={{ marginTop: '4px' }}>
            <code>&gt;&nbsp;</code>
            <span className="cmd-clickable" onClick={() => onRunCommand('graph')}>graph</span>
            <span style={{ color: '#007a33' }}> (alias: </span>
            <span className="cmd-clickable" onClick={() => onRunCommand('g')}>g</span>
            <span style={{ color: '#007a33' }}>)</span>
          </div>
        </div>

        <div style={{ border: '1px solid #007a33', padding: '10px', background: '#000802' }}>
          <h3 style={{ color: '#33ff88', marginBottom: '6px', fontSize: '16px' }}>[2] RAW BYTE &amp; WALLET DOSSIER</h3>
          <p style={{ fontSize: '15px', color: '#00ff66', marginBottom: '6px' }}>
            Inspect raw bytecode, OFAC AML risk metrics, and transaction ledgers for target suspect nodes:
          </p>
          <div style={{ marginTop: '4px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <span className="cmd-clickable" onClick={() => onRunCommand('inspect 0x71C84A9E')}>inspect 0x71C84A9E</span>
            <span className="cmd-clickable" onClick={() => onRunCommand('inspect 0x77DD9900')}>cat 0x77DD9900</span>
          </div>
        </div>

        <div style={{ border: '1px solid #007a33', padding: '10px', background: '#000802' }}>
          <h3 style={{ color: '#33ff88', marginBottom: '6px', fontSize: '16px' }}>[3] MULTI-HOP FUND TRACER</h3>
          <p style={{ fontSize: '15px', color: '#00ff66', marginBottom: '6px' }}>
            Trace laundering routes across hops to see where stolen funds flow:
          </p>
          <div style={{ marginTop: '4px' }}>
            <span className="cmd-clickable" onClick={() => onRunCommand('trace 0x5C8821FF 0xEE3388A1')}>
              trace 0x5C8821FF 0xEE3388A1
            </span>
          </div>
        </div>

        <div style={{ border: '1px solid #007a33', padding: '10px', background: '#000802' }}>
          <h3 style={{ color: '#33ff88', marginBottom: '6px', fontSize: '16px' }}>[4] KERNEL INTERCEPT STREAM</h3>
          <p style={{ fontSize: '15px', color: '#00ff66', marginBottom: '6px' }}>
            Stream live mempool peeling chain detection and darknet blacklist intercepts:
          </p>
          <div style={{ marginTop: '4px' }}>
            <code>&gt;&nbsp;</code>
            <span className="cmd-clickable" onClick={() => onRunCommand('dmesg')}>dmesg</span>
            <span style={{ color: '#007a33' }}> (alias: </span>
            <span className="cmd-clickable" onClick={() => onRunCommand('logs')}>logs</span>
            <span style={{ color: '#007a33' }}>)</span>
          </div>
        </div>
      </div>

      <div style={{ borderTop: '1px dashed #007a33', paddingTop: '10px', fontSize: '15px', color: '#007a33', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <span>Type <span className="cmd-clickable" onClick={() => onRunCommand('help')}>help</span> or <span className="cmd-clickable" onClick={() => onRunCommand('man')}>man</span> for full manual</span>
        <span>Autocompletion: <span style={{ color: '#00ff66' }}>[TAB]</span> | History: <span style={{ color: '#00ff66' }}>[↑ / ↓]</span> | Clear: <span style={{ color: '#00ff66' }}>Ctrl+L</span></span>
      </div>
    </div>
  );
};
