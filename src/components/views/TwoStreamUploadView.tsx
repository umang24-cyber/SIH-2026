import React, { useState, useRef } from 'react';
import { api } from '../../services/api';
import { sound } from '../../audio/soundEngine';

export const TwoStreamUploadView: React.FC = () => {
  const [ledgerFile, setLedgerFile] = useState<File | null>(null);
  const [networkFile, setNetworkFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const ledgerInputRef = useRef<HTMLInputElement>(null);
  const networkInputRef = useRef<HTMLInputElement>(null);

  const handleCorrelate = async () => {
    if (!ledgerFile || !networkFile) {
      setError("Both Ledger and Network Telemetry files are required.");
      sound.playErrorChirp();
      return;
    }
    setError(null);
    setIsUploading(true);
    sound.playEnterSuccess();
    try {
      const res = await api.correlateFiles(ledgerFile, networkFile);
      setResult(res);
      sound.playEnterSuccess();
    } catch (err: any) {
      setError(err.message || 'Correlation failed.');
      sound.playErrorChirp();
    } finally {
      setIsUploading(false);
    }
  };

  if (result) {
    return (
      <div className="output-section">
        <div className="output-header">[SYS] CORRELATION COMPLETE</div>
        <div style={{ color: 'var(--color-primary)' }}>
          <p>Ledger Records: {result.ledger_records}</p>
          <p>Network Records: {result.network_records}</p>
          <p>Matched Records: {result.matched_records}</p>
          <p>Unmatched Ledger: {result.unmatched_ledger}</p>
          <p>Unmatched Network: {result.unmatched_network}</p>
          <p>Correlation Rate: {(result.correlation_rate * 100).toFixed(2)}%</p>
        </div>
      </div>
    );
  }

  return (
    <div className="output-section" style={{ border: '1px solid var(--color-primary)', padding: '10px', marginTop: '10px' }}>
      <div className="output-header" style={{ textAlign: 'center', marginBottom: '15px' }}>CORRELATE & INGEST</div>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div style={{ flex: 1, border: '1px dashed var(--color-primary)', padding: '15px', marginRight: '10px', textAlign: 'center', cursor: 'pointer' }}
             onClick={() => ledgerInputRef.current?.click()}>
          <div style={{ color: 'var(--color-primary)', fontWeight: 'bold' }}>ZONE 1</div>
          <div>BLOCKCHAIN LEDGER</div>
          <div style={{ fontSize: '0.8em', opacity: 0.8 }}>CSV / JSON / XML</div>
          <input type="file" ref={ledgerInputRef} style={{ display: 'none' }} onChange={(e) => setLedgerFile(e.target.files?.[0] || null)} />
          {ledgerFile && <div style={{ marginTop: '10px', color: 'var(--color-accent)' }}>{ledgerFile.name}</div>}
        </div>

        <div style={{ flex: 1, border: '1px dashed var(--color-primary)', padding: '15px', marginLeft: '10px', textAlign: 'center', cursor: 'pointer' }}
             onClick={() => networkInputRef.current?.click()}>
          <div style={{ color: 'var(--color-primary)', fontWeight: 'bold' }}>ZONE 2</div>
          <div>P2P NETWORK TELEMETRY</div>
          <div style={{ fontSize: '0.8em', opacity: 0.8 }}>CSV / JSON / XML</div>
          <input type="file" ref={networkInputRef} style={{ display: 'none' }} onChange={(e) => setNetworkFile(e.target.files?.[0] || null)} />
          {networkFile && <div style={{ marginTop: '10px', color: 'var(--color-accent)' }}>{networkFile.name}</div>}
        </div>
      </div>

      {error && <div style={{ color: 'var(--color-error)', marginBottom: '10px', textAlign: 'center' }}>{error}</div>}

      <div style={{ textAlign: 'center' }}>
        <button 
          onClick={handleCorrelate} 
          disabled={isUploading}
          style={{ 
            background: 'var(--color-primary)', 
            color: 'var(--color-bg)', 
            border: 'none', 
            padding: '10px 20px', 
            cursor: isUploading ? 'wait' : 'pointer',
            fontWeight: 'bold'
          }}>
          {isUploading ? 'CORRELATING...' : '[ CORRELATE & INGEST ]'}
        </button>
      </div>
    </div>
  );
};
