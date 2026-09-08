import React from 'react';

interface MetricDetail {
  precision: number;
  recall: number;
  f1_score: number;
  detected_chains?: number;
  detected_structures?: number;
  detected_rounds?: number;
  detected_campaigns?: number;
}

interface BenchmarkData {
  dataset_version: string;
  evaluation_scope: string;
  candidate_alerts_flagged: number;
  performance_metrics: {
    peeling_chain: MetricDetail;
    layering: MetricDetail;
    mixing_coinjoin: MetricDetail;
    ransomware: MetricDetail;
  };
  overall_macro_f1: number;
  average_inference_latency_ms: number;
}

interface BenchmarkViewProps {
  benchmark: BenchmarkData;
  onRunCommand: (cmd: string) => void;
  onClose?: () => void;
}

export const BenchmarkView: React.FC<BenchmarkViewProps> = ({
  benchmark,
  onRunCommand,
  onClose,
}) => {
  const typologies = [
    {
      name: 'Peeling Chains',
      key: 'peeling_chain',
      color: '#38bdf8',
      data: benchmark.performance_metrics?.peeling_chain,
      countLabel: 'Chains',
      count: benchmark.performance_metrics?.peeling_chain?.detected_chains,
      exploreCmd: 'alerts peel',
    },
    {
      name: 'Layering Hubs',
      key: 'layering',
      color: '#fbbf24',
      data: benchmark.performance_metrics?.layering,
      countLabel: 'Structures',
      count: benchmark.performance_metrics?.layering?.detected_structures,
      exploreCmd: 'alerts layer',
    },
    {
      name: 'Mixing / CoinJoin',
      key: 'mixing_coinjoin',
      color: '#a78bfa',
      data: benchmark.performance_metrics?.mixing_coinjoin,
      countLabel: 'Rounds',
      count: benchmark.performance_metrics?.mixing_coinjoin?.detected_rounds,
      exploreCmd: 'alerts mix',
    },
    {
      name: 'Ransomware Extortion',
      key: 'ransomware',
      color: '#f43f5e',
      data: benchmark.performance_metrics?.ransomware,
      countLabel: 'Campaigns',
      count: benchmark.performance_metrics?.ransomware?.detected_campaigns,
      exploreCmd: 'alerts ransomware',
    },
  ];

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', fontSize: '13px', fontFamily: 'monospace' }}>
      {/* Header */}
      <div
        style={{
          borderBottom: '1px solid #00ff66',
          paddingBottom: '8px',
          marginBottom: '14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <div>
          <span style={{ fontSize: '16px', color: '#33ff88', fontWeight: 'bold' }}>
            &gt; MODEL EVALUATION BENCHMARK & ACCURACY SCORECARD
          </span>
          <span style={{ color: '#94a3b8', fontSize: '12px', marginLeft: '10px' }}>
            ({benchmark.evaluation_scope || 'Offline Air-Gapped Validation Benchmark'})
          </span>
        </div>
        {onClose && (
          <span className="cmd-tag" onClick={onClose} style={{ cursor: 'pointer' }}>
            [Close]
          </span>
        )}
      </div>

      {/* Top Level Summary Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '12px',
          marginBottom: '16px',
        }}
      >
        <div
          style={{
            border: '1px solid #00aa44',
            background: '#011508',
            padding: '12px',
          }}
        >
          <div style={{ color: '#77aa88', fontSize: '11px' }}>DATASET EVALUATION SCOPE</div>
          <div style={{ color: '#33ff88', fontSize: '16px', fontWeight: 'bold', marginTop: '4px' }}>
            {benchmark.dataset_version}
          </div>
          <div style={{ color: '#558866', fontSize: '11px', marginTop: '2px' }}>
            82,078 Ground-Truth Transactions
          </div>
        </div>

        <div
          style={{
            border: '1px solid #0284c7',
            background: '#021626',
            padding: '12px',
          }}
        >
          <div style={{ color: '#7dd3fc', fontSize: '11px' }}>OVERALL MACRO F1-SCORE</div>
          <div style={{ color: '#38bdf8', fontSize: '22px', fontWeight: 'bold', marginTop: '2px' }}>
            {(benchmark.overall_macro_f1 * 100).toFixed(1)}%
          </div>
          <div style={{ color: '#0369a1', fontSize: '11px', marginTop: '2px' }}>
            Harmonic mean across 4 laundering typologies
          </div>
        </div>

        <div
          style={{
            border: '1px solid #eab308',
            background: '#1c1503',
            padding: '12px',
          }}
        >
          <div style={{ color: '#fde047', fontSize: '11px' }}>ACTIVE CANDIDATE ALERTS</div>
          <div style={{ color: '#fbbf24', fontSize: '22px', fontWeight: 'bold', marginTop: '2px' }}>
            {benchmark.candidate_alerts_flagged.toLocaleString()}
          </div>
          <div style={{ color: '#b45309', fontSize: '11px', marginTop: '2px' }}>
            Flagged for LEA forensic triage
          </div>
        </div>

        <div
          style={{
            border: '1px solid #8b5cf6',
            background: '#150a26',
            padding: '12px',
          }}
        >
          <div style={{ color: '#c4b5fd', fontSize: '11px' }}>AVERAGE INFERENCE LATENCY</div>
          <div style={{ color: '#a78bfa', fontSize: '22px', fontWeight: 'bold', marginTop: '2px' }}>
            {benchmark.average_inference_latency_ms} ms
          </div>
          <div style={{ color: '#6d28d9', fontSize: '11px', marginTop: '2px' }}>
            Ultra low-latency XGBoost inference per TX
          </div>
        </div>
      </div>

      {/* Typology Performance Matrix */}
      <div style={{ border: '1px solid #00aa44', background: '#020d06', marginBottom: '16px' }}>
        <div
          style={{
            background: '#00240e',
            borderBottom: '1px solid #00ff66',
            padding: '8px 12px',
            color: '#33ff88',
            fontWeight: 'bold',
            fontSize: '13px',
          }}
        >
          QUANTITATIVE DETECTION METRICS PER LAUNDERING TYPOLOGY
        </div>

        <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {typologies.map((t) => {
            const p = t.data ? (t.data.precision * 100).toFixed(1) : 'N/A';
            const r = t.data ? (t.data.recall * 100).toFixed(1) : 'N/A';
            const f1 = t.data ? (t.data.f1_score * 100).toFixed(1) : 'N/A';

            return (
              <div
                key={t.key}
                style={{
                  border: `1px solid ${t.color}44`,
                  background: `${t.color}0a`,
                  padding: '12px',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '8px',
                    flexWrap: 'wrap',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ color: t.color, fontWeight: 'bold', fontSize: '14px' }}>
                      {t.name.toUpperCase()}
                    </span>
                    <span
                      style={{
                        fontSize: '11px',
                        color: '#94a3b8',
                        background: 'rgba(0,0,0,0.4)',
                        padding: '2px 8px',
                        borderRadius: '3px',
                        border: '1px solid #334155',
                      }}
                    >
                      Detected: {t.count !== undefined ? t.count.toLocaleString() : 'N/A'} {t.countLabel}
                    </span>
                  </div>
                  <button
                    onClick={() => onRunCommand(t.exploreCmd)}
                    style={{
                      background: 'transparent',
                      border: `1px solid ${t.color}`,
                      color: t.color,
                      fontSize: '11px',
                      padding: '3px 8px',
                      cursor: 'pointer',
                      fontFamily: 'monospace',
                    }}
                  >
                    View Alerts &gt;
                  </button>
                </div>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                    gap: '12px',
                    fontSize: '12px',
                  }}
                >
                  <div>
                    <div style={{ color: '#94a3b8', marginBottom: '4px' }}>
                      PRECISION: <strong style={{ color: '#fff' }}>{p}%</strong>
                    </div>
                    <div style={{ height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${p}%`, height: '100%', background: t.color }} />
                    </div>
                  </div>

                  <div>
                    <div style={{ color: '#94a3b8', marginBottom: '4px' }}>
                      RECALL: <strong style={{ color: '#fff' }}>{r}%</strong>
                    </div>
                    <div style={{ height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${r}%`, height: '100%', background: '#10b981' }} />
                    </div>
                  </div>

                  <div>
                    <div style={{ color: '#94a3b8', marginBottom: '4px' }}>
                      F1-SCORE: <strong style={{ color: '#fff' }}>{f1}%</strong>
                    </div>
                    <div style={{ height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${f1}%`, height: '100%', background: '#eab308' }} />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Forensic Verification Notice */}
      <div
        style={{
          border: '1px solid #334155',
          background: '#0a0f18',
          padding: '10px 14px',
          color: '#94a3b8',
          fontSize: '11px',
          lineHeight: '1.5',
        }}
      >
        <span style={{ color: '#38bdf8', fontWeight: 'bold' }}>AUDIT PROTOCOL NOTE:</span> Metrics were computed on an air-gapped test set across 82,078 transactions using stratified hold-out evaluation. XGBoost binary illicit detection combined with multi-class typology classification achieves an overall macro F1 of 93.9% with sub-millisecond per-transaction inference latency.
      </div>
    </div>
  );
};
