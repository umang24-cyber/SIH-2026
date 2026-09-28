import React from 'react';
import './CorrelationEvidencePanel.css';

export interface CorrelationEvidence {
  transaction_hash: string;
  match_method: string;
  match_status: string;
  ledger_timestamp: string | null;
  timing_delta_seconds: number | null;
  timing_status: string;
  correlation_confidence: null;
  attribution_status: string;
  observations: { relay_timestamp: string | null; relay_ip: string | null; asn: string | null; node_type: string | null }[];
  reasons: string[];
}

type Phase = 'idle' | 'loading' | 'error' | 'complete';
interface Props {
  phase: Phase;
  evidence?: CorrelationEvidence[] | null;
}

const readable = (value?: string | null) => value ? value.replace(/_/g, ' ') : 'Not provided';

export function CorrelationEvidencePanel({ phase, evidence }: Props) {
  const rows = Array.isArray(evidence) ? evidence : [];
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
        <p className="correlation-confidence"><strong>Correlation confidence:</strong> <span>Not estimated</span></p>
      </header>
      <p className="correlation-evidence-note">
        A validated numeric correlation probability is not available. Match coverage and V8 risk/typology scores are separate metrics, not correlation confidence.
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
                  <dl className="correlation-evidence-fields">
                    <div><dt>Match Method</dt><dd>{readable(item.match_method)}</dd></div>
                    <div><dt>Timing Status</dt><dd>{readable(item.timing_status)}</dd></div>
                    <div><dt>Ledger Timestamp</dt><dd>{item.ledger_timestamp || 'Not observed'}</dd></div>
                    <div><dt>Observed Time Gap</dt><dd>{delta}</dd></div>
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
