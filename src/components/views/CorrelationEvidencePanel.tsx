import React from 'react';
import './CorrelationEvidencePanel.css';

export interface CorrelationEvidence {
  transaction_hash: string;
  txid?: number | null;
  scenario_id?: string | null;
  match_method: string;
  match_status: string;
  ledger_timestamp: string | null;
  timing_delta_seconds: number | null;
  timing_status: string;
  correlation_confidence: number | null;
  attribution_status: string;
  observations: { relay_timestamp: string | null; relay_ip: string | null; asn: string | null; node_type: string | null }[];
  reasons: string[];
}

type Phase = 'idle' | 'loading' | 'error' | 'complete';
interface Props {
  phase: Phase;
  evidence?: CorrelationEvidence[] | null;
  overallConfidence?: number | null;
  onRunCommand?: (cmd: string) => void;
}

const readable = (value?: string | null) => value ? value.replace(/_/g, ' ') : 'Not provided';

export function CorrelationEvidencePanel({ phase, evidence, overallConfidence, onRunCommand }: Props) {
  const rows = Array.isArray(evidence) ? evidence : [];
  const validConfidences = rows
    .map(r => r.correlation_confidence)
    .filter((c): c is number => typeof c === 'number' && Number.isFinite(c));

  const confidenceScore = typeof overallConfidence === 'number' && Number.isFinite(overallConfidence)
    ? overallConfidence
    : validConfidences.length > 0
      ? validConfidences.reduce((a, b) => a + b, 0) / validConfidences.length
      : null;

  const message = phase === 'loading'
    ? 'Correlating the uploaded streams. Evidence will appear when the backend responds.'
    : phase === 'error'
      ? 'Correlation could not complete. Resolve the upload error and retry to see evidence.'
      : phase === 'idle'
        ? 'Upload both files and run correlation to see the actual match evidence here.'
        : Array.isArray(evidence)
          ? 'No correlation evidence was returned for this upload. No match or timing result is assumed.'
          : 'This backend response does not include correlation evidence. Restart the updated backend and upload again.';
  const placeholder = phase === 'idle' ? 'Awaiting upload' : phase === 'loading' ? 'Pending analysis' : 'Not available';

  return (
    <section className="correlation-evidence-panel" aria-label="Evidence & Correlation Analysis" aria-busy={phase === 'loading'}>
      <header className="correlation-evidence-header">
        <h3>Evidence &amp; Correlation Analysis</h3>
        <p className="correlation-confidence">
          <strong>Correlation confidence:</strong>{' '}
          <span>
            {confidenceScore !== null
              ? `${(confidenceScore * 100).toFixed(1)}% (XGBoost V8)`
              : phase === 'loading'
                ? 'Computing XGBoost inference...'
                : phase === 'idle'
                  ? 'Awaiting dual-stream correlation'
                  : 'Not estimated'}
          </span>
        </p>
      </header>
      <p className="correlation-evidence-note">
        {confidenceScore !== null
          ? 'Dual-stream correlation evaluated directly through V8 XGBoost ML inference using graph, timing, and P2P relay features.'
          : 'A validated numeric correlation probability is not available. Match coverage and V8 risk/typology scores are separate metrics, not correlation confidence.'}
      </p>
      {rows.length === 0 ? (
        <>
          <p className="correlation-evidence-status" role="status">{message}</p>
          <dl className="correlation-evidence-fields">
            <div><dt>Match Method</dt><dd>{placeholder}</dd></div>
            <div><dt>Timing Status</dt><dd>{placeholder}</dd></div>
            <div><dt>Observations</dt><dd>{phase === 'idle' ? 'Relay timestamps and sources appear after correlation.' : placeholder}</dd></div>
            <div><dt>Reasons</dt><dd>{phase === 'idle' ? 'Backend evidence and limitations appear after correlation.' : placeholder}</dd></div>
          </dl>
        </>
      ) : (
        <>
          <p className="correlation-evidence-status" role="status">{rows.length} evidence record{rows.length === 1 ? '' : 's'}. First record expanded; select another transaction to review it.</p>
          <div className="correlation-evidence-records">
            {rows.map((item, index) => {
              const observations = Array.isArray(item.observations) ? item.observations : [];
              const reasons = Array.isArray(item.reasons) ? item.reasons : [];
              const delta = typeof item.timing_delta_seconds === 'number' && Number.isFinite(item.timing_delta_seconds)
                ? `${item.timing_delta_seconds}s (signed)` : 'Not observed';
              return (
                <details key={`${item.transaction_hash}-${index}`} open={index === 0} className="correlation-evidence-record">
                  <summary>{item.transaction_hash || 'Transaction ID not provided'} · {readable(item.match_status)}</summary>
                  
                  {onRunCommand && (
                    <div style={{ display: 'flex', gap: '8px', margin: '8px 0', flexWrap: 'wrap' }}>
                      <button
                        onClick={(e) => { e.stopPropagation(); onRunCommand(`graph ${item.transaction_hash}`); }}
                        style={{
                          background: '#002b11',
                          border: '1px solid #00ff66',
                          color: '#00ff66',
                          padding: '4px 9px',
                          fontSize: '11px',
                          cursor: 'pointer',
                          fontWeight: 'bold',
                          fontFamily: 'inherit',
                          borderRadius: '2px'
                        }}
                      >
                        🌐 View in 3D Graph
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); onRunCommand(`inspect ${item.transaction_hash}`); }}
                        style={{
                          background: '#001a2b',
                          border: '1px solid #33aaff',
                          color: '#33aaff',
                          padding: '4px 9px',
                          fontSize: '11px',
                          cursor: 'pointer',
                          fontWeight: 'bold',
                          fontFamily: 'inherit',
                          borderRadius: '2px'
                        }}
                      >
                        🔍 Inspect TX
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); onRunCommand(`flow ${item.transaction_hash}`); }}
                        style={{
                          background: '#2b1a00',
                          border: '1px solid #ffaa33',
                          color: '#ffaa33',
                          padding: '4px 9px',
                          fontSize: '11px',
                          cursor: 'pointer',
                          fontWeight: 'bold',
                          fontFamily: 'inherit',
                          borderRadius: '2px'
                        }}
                      >
                        🌊 Flow
                      </button>
                    </div>
                  )}

                  <dl className="correlation-evidence-fields">
                    <div><dt>Match Method</dt><dd>{readable(item.match_method)}</dd></div>
                    <div><dt>Timing Status</dt><dd>{readable(item.timing_status)}</dd></div>
                    <div><dt>Ledger Timestamp</dt><dd>{item.ledger_timestamp || 'Not observed'}</dd></div>
                    <div><dt>Observed Time Gap</dt><dd>{delta}</dd></div>
                    <div>
                      <dt>Correlation Confidence</dt>
                      <dd>
                        {item.correlation_confidence !== null && item.correlation_confidence !== undefined
                          ? `${(item.correlation_confidence * 100).toFixed(1)}% (XGBoost)`
                          : 'Not estimated'}
                      </dd>
                    </div>
                    {item.scenario_id && (
                      <div>
                        <dt>Scenario Cluster</dt>
                        <dd>
                          <span
                            style={{ color: '#00ffaa', cursor: onRunCommand ? 'pointer' : 'default', textDecoration: onRunCommand ? 'underline' : 'none' }}
                            onClick={() => onRunCommand?.(`graph ${item.scenario_id}`)}
                            title="Click to view scenario in 3D graph"
                          >
                            {item.scenario_id}
                          </span>
                        </dd>
                      </div>
                    )}
                  </dl>
                  <p className="correlation-evidence-note">Time gap = ledger timestamp minus earliest valid relay observation; it does not measure a sender's intentional delay.</p>
                  <h4>Observations</h4>
                  {observations.length ? (
                    <ul className="correlation-observations" aria-label={`Relay observations for ${item.transaction_hash}`}>
                      {observations.map((obs, i) => <li key={i}>
                        <strong>Relay observation {i + 1}</strong>: {obs.relay_timestamp || 'Timestamp missing'}
                        <br />IP: {obs.relay_ip || 'Unknown'} · ASN: {obs.asn || 'Unknown'} · Infrastructure: {readable(obs.node_type)}
                      </li>)}
                    </ul>
                  ) : <p>No relay observations returned for this record.</p>}
                  <h4>Reasons</h4>
                  {reasons.length ? <ul className="correlation-reasons">{reasons.map((reason, i) => <li key={i}>{reason}</li>)}</ul>
                    : <p>No reasons were provided by the backend.</p>}
                  <p className="correlation-evidence-note"><strong>Sender attribution:</strong> {readable(item.attribution_status)}</p>
                </details>
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}
