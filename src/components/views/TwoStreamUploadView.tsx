import React, { useState, useRef, useEffect } from 'react';
import { api } from '../../services/api';
import { sound } from '../../audio/soundEngine';
import { CorrelationEvidencePanel } from './CorrelationEvidencePanel';

interface TwoStreamUploadViewProps {
  onRunCommand?: (cmd: string) => void;
  onClose?: () => void;
}

const SAMPLE_LEDGER_CSV = `txid,timestamp,input_addresses,output_addresses,input_amounts,output_amounts,fee_btc,script_type,scenario_id
881920041,2026-09-06 14:22:10,"[""1AtB5eWkX36d4YtQ99vK8h7G4xN19mK7p""]","[""1Lq9QkX4p82YtMw3B7vH29zR6cE81nM3b"",""1Vp4Qw98mNtK32bRx87hG21yE94xC65pK""]","[12.45]","[12.4485,0.001]",0.0005,P2PKH,live_ransomware_probe
881920042,2026-09-06 14:25:30,"[""1Lq9QkX4p82YtMw3B7vH29zR6cE81nM3b""]","[""1RansomMuleHop01_8819"",""1RansomCarryHop01_8819""]","[12.4485]","[6.2,6.248]",0.0005,P2SH,live_ransomware_probe
992019342,2026-09-06 15:10:00,"[""1PeelOriginSource99281hKx38v92""]","[""1PeelHopOneTarget99281hKx38v92"",""1PeelChangeAddressCarry99281hK""]","[50.0]","[1.5,48.4998]",0.0002,P2PKH,live_peeling_sequence
992019343,2026-09-06 15:15:12,"[""1PeelChangeAddressCarry99281hK""]","[""1PeelHopTwoTarget88291"",""1PeelChangeAddressCarry2_99""]","[48.4998]","[2.5,45.9996]",0.0002,P2PKH,live_peeling_sequence
771029341,2026-09-06 16:05:30,"[""1MixInputPartyA_981729381kKx"",""1MixInputPartyB_881729382bBx"",""1MixInputPartyC_771729383cCx"",""1MixInputPartyD_661729384dDx""]","[""1MixEqualOut1_991827391aAx"",""1MixEqualOut2_881827392bBx"",""1MixEqualOut3_771827393cCx"",""1MixEqualOut4_661827394dDx""]","[0.55,0.53,0.54,0.56]","[0.5,0.5,0.5,0.5]",0.0004,P2SH,live_coinjoin_round
551029482,2026-09-06 17:00:15,"[""1LicitConsumerWallet88291kKx99""]","[""1LicitMerchantStorefront77291aA"",""1LicitChangeWallet88291kKx99""]","[0.15]","[0.045,0.1049]",0.0001,P2WPKH,live_licit_purchase`;

const SAMPLE_NETWORK_CSV = `txid,relay_timestamp,relay_ip,relay_port,node_type,country_code,asn,isp,protocol_version,user_agent
881920041,2026-09-06 14:22:08,185.220.101.44,9050,bulletproof_host,RU,AS49981,WorldStream B.V. Bulletproof Relay,70015,/Satoshi:22.0.0/
881920042,2026-09-06 14:25:28,185.220.101.50,9050,tor_exit_node,RU,AS49981,WorldStream B.V. Bulletproof Relay,70015,/Satoshi:22.0.0/
992019342,2026-09-06 15:09:59,194.26.29.112,8333,vpn_proxy,PA,AS60068,Datacenter Transit Proxy,70015,/Satoshi:22.0.0/
992019343,2026-09-06 15:15:11,194.26.29.115,8333,vpn_proxy,PA,AS60068,Datacenter Transit Proxy,70015,/Satoshi:22.0.0/
771029341,2026-09-06 16:05:29,104.244.76.13,8333,tor_exit_node,DE,AS200651,Tor Relay Exit Operator,70015,/Satoshi:22.0.0/
551029482,2026-09-06 17:00:15,73.189.44.201,8333,residential,US,AS7922,Comcast Cable Communications,70015,/Satoshi:22.0.0/`;

export const TwoStreamUploadView: React.FC<TwoStreamUploadViewProps> = ({ onRunCommand, onClose }) => {
  const [ledgerFile, setLedgerFile] = useState<File | null>(null);
  const [networkFile, setNetworkFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const ledgerInputRef = useRef<HTMLInputElement>(null);
  const networkInputRef = useRef<HTMLInputElement>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (result) resultRef.current?.scrollIntoView({ block: 'start', behavior: 'auto' });
  }, [result]);

  const handleLoadDemoFiles = async () => {
    try {
      const pair = await api.getIngestSamplePair();
      if (pair?.ledger_csv && pair?.network_csv) {
        setLedgerFile(new File([pair.ledger_csv], "sample_blockchain_ledger.csv", { type: "text/csv" }));
        setNetworkFile(new File([pair.network_csv], "sample_p2p_network_telemetry.csv", { type: "text/csv" }));
        setError(null);
        sound.playEnterSuccess();
        return;
      }
    } catch {
      // fallback to pre-baked constants
    }
    const lFile = new File([SAMPLE_LEDGER_CSV], "sample_blockchain_ledger.csv", { type: "text/csv" });
    const nFile = new File([SAMPLE_NETWORK_CSV], "sample_p2p_network_telemetry.csv", { type: "text/csv" });
    setLedgerFile(lFile);
    setNetworkFile(nFile);
    setError(null);
    sound.playEnterSuccess();
  };

  const handleCorrelate = async () => {
    if (!ledgerFile || !networkFile) {
      setError("Both Blockchain Ledger (Stream 1) and Network Telemetry (Stream 2) files are required.");
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

  const getTypologyColor = (typ: string | undefined, isIllicit?: boolean) => {
    if (!isIllicit) return '#00ff66';
    const t = (typ || '').toLowerCase();
    if (t.includes('ransom')) return '#ff3355';
    if (t.includes('peel')) return '#ff8800';
    if (t.includes('layer')) return '#ffcc00';
    if (t.includes('mix')) return '#bb44ff';
    return '#ff4455';
  };

  if (result) {
    const correlationPct = (result.correlation_rate * 100).toFixed(1);
    const scenarioList = result.scenario_results || [];

    return (
      <div ref={resultRef} className="output-block" style={{
        background: 'rgba(3, 10, 6, 0.95)',
        border: '1px solid #00aa44',
        boxShadow: '0 0 20px rgba(0, 255, 102, 0.15)',
        padding: '16px',
        marginBottom: '16px',
        borderRadius: '4px',
        fontFamily: 'inherit'
      }}>
        {/* Header Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #005522', paddingBottom: '10px', marginBottom: '14px' }}>
          <div>
            <div style={{ color: '#00ff66', fontWeight: 'bold', fontSize: '15px', letterSpacing: '1px' }}>
              ⚡ DUAL-LAYER INGESTION &amp; V8 CORRELATION ENGINE COMPLETE
            </div>
            <div style={{ color: '#88bb99', fontSize: '11px', marginTop: '2px' }}>
              Outer join on txid merged on-chain UTXO state + P2P broadcast telemetry into unified forensic graph.
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => { setResult(null); sound.playEnterSuccess(); }}
              style={{
                background: 'transparent',
                border: '1px solid #00aa44',
                color: '#33ff88',
                padding: '4px 10px',
                fontSize: '11px',
                cursor: 'pointer',
                fontFamily: 'inherit'
              }}
            >
              [↺ Ingest Another Pair]
            </button>
            {onClose && (
              <button
                onClick={onClose}
                style={{
                  background: 'transparent',
                  border: '1px solid #555',
                  color: '#888',
                  padding: '4px 8px',
                  fontSize: '11px',
                  cursor: 'pointer',
                  fontFamily: 'inherit'
                }}
              >
                [✕]
              </button>
            )}
          </div>
        </div>

        <CorrelationEvidencePanel phase="complete" evidence={result.correlation_evidence} />

        {/* Telemetry Summary Stats */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '10px',
          background: 'rgba(0, 25, 10, 0.6)',
          padding: '10px',
          border: '1px solid #00441a',
          marginBottom: '16px',
          fontSize: '12px'
        }}>
          <div>
            <div style={{ color: '#66aa88', fontSize: '10px' }}>LEDGER TXS</div>
            <div style={{ color: '#fff', fontSize: '16px', fontWeight: 'bold' }}>{result.ledger_records}</div>
          </div>
          <div>
            <div style={{ color: '#66aa88', fontSize: '10px' }}>P2P TELEMETRY TXS</div>
            <div style={{ color: '#fff', fontSize: '16px', fontWeight: 'bold' }}>{result.network_records}</div>
          </div>
          <div>
            <div style={{ color: '#66aa88', fontSize: '10px' }}>EXACT-ID MATCH COVERAGE</div>
            <div style={{ color: '#33ff88', fontSize: '16px', fontWeight: 'bold' }}>{result.matched_records} ({correlationPct}%)</div>
          </div>
          <div>
            <div style={{ color: '#66aa88', fontSize: '10px' }}>NEWLY INDEXED</div>
            <div style={{ color: '#aaffaa', fontSize: '16px', fontWeight: 'bold' }}>{result.newly_indexed_records}</div>
          </div>
          <div>
            <div style={{ color: '#66aa88', fontSize: '10px' }}>UNMATCHED STREAMS</div>
            <div style={{ color: '#ffaa33', fontSize: '16px', fontWeight: 'bold' }}>{result.unmatched_ledger + result.unmatched_network}</div>
          </div>
          <div>
            <div style={{ color: '#66aa88', fontSize: '10px' }}>TIMING ISSUES / CONFLICTS</div>
            <div style={{ color: '#ffaa33', fontSize: '16px', fontWeight: 'bold' }}>{result.timing_issue_count ?? 0} / {result.conflicting_records ?? 0}</div>
          </div>
        </div>

        <div style={{ color: '#88bb99', fontSize: '11px', marginBottom: '12px' }}>
          Coverage is the fraction of records sharing an original transaction ID, not a confidence score. Relay observations do not verify the sender.
        </div>

        {/* Scenarios Analyzed */}
        <div style={{ color: '#33ff88', fontWeight: 'bold', fontSize: '13px', marginBottom: '8px', letterSpacing: '0.5px' }}>
          [*] V8 MACHINE LEARNING THREAT EVALUATION ({scenarioList.length} Scenario Clusters)
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {scenarioList.map((sc: any, idx: number) => {
            const isAvail = sc.analysis_status === 'AVAILABLE';
            const riskPct = sc.risk_score !== null && sc.risk_score !== undefined ? (sc.risk_score * 100).toFixed(1) : 'N/A';
            const isIllicit = Boolean(sc.is_illicit);
            const typ = sc.predicted_typology || (isIllicit ? 'UNKNOWN' : 'NORMAL');
            const typColor = getTypologyColor(typ, isIllicit);
            const typConfPct = sc.typology_confidence !== null && sc.typology_confidence !== undefined ? (sc.typology_confidence * 100).toFixed(1) : null;
            const anomScore = sc.anomaly_score !== null && sc.anomaly_score !== undefined ? Number(sc.anomaly_score).toFixed(1) : null;

            return (
              <div
                key={sc.scenario_id || idx}
                style={{
                  background: 'rgba(5, 18, 10, 0.85)',
                  border: `1px solid ${typColor}`,
                  borderRadius: '3px',
                  padding: '12px',
                  boxShadow: `0 0 10px ${typColor}22`
                }}
              >
                {/* Scenario Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{
                      background: `${typColor}22`,
                      color: typColor,
                      border: `1px solid ${typColor}`,
                      padding: '2px 8px',
                      fontSize: '11px',
                      fontWeight: 'bold',
                      borderRadius: '2px'
                    }}>
                      {isIllicit ? `⚠️ ${typ.toUpperCase()} THREAT` : '🛡️ LICIT ACTIVITY'}
                    </span>
                    <span style={{ color: '#ffffff', fontWeight: 'bold', fontSize: '14px' }}>
                      Scenario: {sc.scenario_id}
                    </span>
                    <span style={{ color: '#888', fontSize: '11px' }}>
                      ({sc.transaction_count} transactions merged)
                    </span>
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    {onRunCommand && (
                      <>
                        <button
                          onClick={() => { sound.playEnterSuccess(); onRunCommand(`graph ${sc.scenario_id}`); }}
                          style={{
                            background: '#003311',
                            border: '1px solid #00ff66',
                            color: '#00ff66',
                            padding: '3px 9px',
                            fontSize: '11px',
                            cursor: 'pointer',
                            fontWeight: 'bold',
                            fontFamily: 'inherit'
                          }}
                        >
                          🌐 Open in 3D Graph
                        </button>
                        <button
                          onClick={() => { sound.playEnterSuccess(); onRunCommand(`inspect ${sc.scenario_id}`); }}
                          style={{
                            background: 'transparent',
                            border: '1px solid #00aa44',
                            color: '#33ff88',
                            padding: '3px 8px',
                            fontSize: '11px',
                            cursor: 'pointer',
                            fontFamily: 'inherit'
                          }}
                        >
                          🔍 Inspect
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {isAvail ? (
                  <>
                    {/* Metrics Bar */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', marginTop: '8px', fontSize: '12px' }}>
                      <div style={{ background: 'rgba(0,0,0,0.4)', padding: '8px', borderLeft: `3px solid ${typColor}` }}>
                        <div style={{ color: '#888', fontSize: '10px' }}>V8 BINARY RISK SCORE P(illicit)</div>
                        <div style={{ color: typColor, fontSize: '15px', fontWeight: 'bold' }}>{riskPct}%</div>
                        <div style={{ width: '100%', height: '4px', background: '#222', marginTop: '4px', borderRadius: '2px', overflow: 'hidden' }}>
                          <div style={{ width: `${Math.min(100, Math.max(0, Number(riskPct)))}%`, height: '100%', background: typColor }} />
                        </div>
                      </div>

                      {typConfPct && (
                        <div style={{ background: 'rgba(0,0,0,0.4)', padding: '8px', borderLeft: '3px solid #ffaa00' }}>
                          <div style={{ color: '#888', fontSize: '10px' }}>TYPOLOGY CONFIDENCE</div>
                          <div style={{ color: '#ffaa00', fontSize: '15px', fontWeight: 'bold' }}>{typConfPct}% ({typ.toUpperCase()})</div>
                          <div style={{ width: '100%', height: '4px', background: '#222', marginTop: '4px', borderRadius: '2px', overflow: 'hidden' }}>
                            <div style={{ width: `${Math.min(100, Math.max(0, Number(typConfPct)))}%`, height: '100%', background: '#ffaa00' }} />
                          </div>
                        </div>
                      )}

                      {anomScore !== null && (
                        <div style={{ background: 'rgba(0,0,0,0.4)', padding: '8px', borderLeft: '3px solid #33bbff' }}>
                          <div style={{ color: '#888', fontSize: '10px' }}>ISOLATION FOREST ANOMALY (0–100)</div>
                          <div style={{ color: Number(anomScore) >= 70 ? '#ff4455' : '#33bbff', fontSize: '15px', fontWeight: 'bold' }}>
                            {anomScore} <span style={{ fontSize: '11px', fontWeight: 'normal' }}>[{sc.anomaly_label || 'NORMAL'}]</span>
                          </div>
                          <div style={{ width: '100%', height: '4px', background: '#222', marginTop: '4px', borderRadius: '2px', overflow: 'hidden' }}>
                            <div style={{ width: `${Math.min(100, Math.max(0, Number(anomScore)))}%`, height: '100%', background: Number(anomScore) >= 70 ? '#ff4455' : '#33bbff' }} />
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Typology Explanation */}
                    {sc.typology_explanation && (
                      <div style={{ marginTop: '10px', fontSize: '12px', color: '#cce6d0', background: 'rgba(0, 30, 15, 0.5)', padding: '8px', borderLeft: '2px solid #00ff66' }}>
                        <strong style={{ color: '#33ff88' }}>Forensic Typology Rationale:</strong> {sc.typology_explanation}
                      </div>
                    )}

                    {/* SHAP Feature Attributions */}
                    {sc.top_shap_attributions && sc.top_shap_attributions.length > 0 && (
                      <div style={{ marginTop: '10px' }}>
                        <div style={{ fontSize: '11px', color: '#88bb99', fontWeight: 'bold', marginBottom: '4px' }}>
                          KEY XGBOOST TREESHAP INFLUENCE FACTORS:
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '6px' }}>
                          {sc.top_shap_attributions.slice(0, 4).map((attr: any, aIdx: number) => {
                            const isElev = attr.direction === 'ELEVATES_RISK' || attr.direction === 'RISK_INCREASING';
                            return (
                              <div
                                key={aIdx}
                                style={{
                                  background: 'rgba(0,0,0,0.5)',
                                  padding: '5px 8px',
                                  fontSize: '11px',
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center',
                                  borderLeft: `2px solid ${isElev ? '#ff5544' : '#00ff66'}`
                                }}
                              >
                                <span style={{ color: '#ddd' }}>{attr.plain_name || attr.feature_name}</span>
                                <span style={{ color: isElev ? '#ff6655' : '#33ff88', fontWeight: 'bold' }}>
                                  {isElev ? '▲ +' : '▼ -'}{Math.abs(Number(attr.attribution_value || attr.shap_value || 0)).toFixed(3)}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div style={{ color: '#ffbb44', fontSize: '12px', marginTop: '6px', fontStyle: 'italic' }}>
                    {sc.analysis_message || 'ML model evaluation pending or unavailable for this sample size.'}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Pre-upload Staging View
  return (
    <div className="output-block" style={{
      background: 'rgba(2, 8, 4, 0.95)',
      border: '1px solid #00aa44',
      padding: '16px',
      marginTop: '10px',
      marginBottom: '16px',
      borderRadius: '4px',
      boxShadow: '0 0 20px rgba(0, 255, 102, 0.1)'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #005522', paddingBottom: '10px', marginBottom: '14px' }}>
        <div>
          <div style={{ color: '#00ff66', fontWeight: 'bold', fontSize: '15px', letterSpacing: '1px' }}>
            ⚡ DUAL-STREAM FORENSIC DATA INGESTION (V8 PIPELINE)
          </div>
          <div style={{ color: '#88bb99', fontSize: '11px', marginTop: '2px' }}>
            Select or drag <strong>Blockchain Ledger (Stream 1)</strong> and <strong>P2P Network Telemetry (Stream 2)</strong> to correlate on <code>txid</code> and run V8 ML inference.
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: '1px solid #555',
              color: '#888',
              padding: '3px 8px',
              fontSize: '11px',
              cursor: 'pointer',
              fontFamily: 'inherit'
            }}
          >
            [✕]
          </button>
        )}
      </div>

      <CorrelationEvidencePanel phase={isUploading ? 'loading' : error ? 'error' : 'idle'} />

      {/* 1-Click Demo Preset Banner */}
      <div style={{
        background: 'rgba(0, 35, 15, 0.7)',
        border: '1px dashed #00cc55',
        padding: '10px 14px',
        marginBottom: '16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderRadius: '3px'
      }}>
        <div style={{ fontSize: '12px', color: '#cce6d0' }}>
          <strong style={{ color: '#33ff88' }}>[DEMO BENCHMARK PRESET]:</strong> Want to test dual-layer correlation instantly without manual CSVs?
        </div>
        <button
          onClick={handleLoadDemoFiles}
          style={{
            background: '#00441a',
            border: '1px solid #00ff66',
            color: '#00ff66',
            padding: '5px 12px',
            fontSize: '11px',
            fontWeight: 'bold',
            cursor: 'pointer',
            fontFamily: 'inherit',
            borderRadius: '2px'
          }}
        >
          ⚡ Load Sample Dual-Stream Pair
        </button>
      </div>

      {/* Dual Upload Zones */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '20px' }}>
        {/* ZONE 1: Blockchain Ledger */}
        <div
          style={{
            border: ledgerFile ? '1px solid #00ff66' : '1px dashed #008833',
            background: ledgerFile ? 'rgba(0, 40, 18, 0.4)' : 'rgba(0, 15, 8, 0.6)',
            padding: '18px',
            textAlign: 'center',
            cursor: 'pointer',
            borderRadius: '3px',
            transition: 'all 0.2s ease'
          }}
          onClick={() => ledgerInputRef.current?.click()}
        >
          <div style={{ color: '#00ff66', fontWeight: 'bold', fontSize: '13px', letterSpacing: '1px' }}>
            ZONE 1: ON-CHAIN BLOCKCHAIN LEDGER
          </div>
          <div style={{ color: '#fff', fontSize: '12px', marginTop: '4px' }}>
            UTXO Inputs / Outputs, Amounts &amp; Fees
          </div>
          <div style={{ fontSize: '11px', color: '#77aa88', marginTop: '4px' }}>
            Accepts CSV, JSON, or XML format
          </div>

          <input
            type="file"
            ref={ledgerInputRef}
            style={{ display: 'none' }}
            onChange={(e) => setLedgerFile(e.target.files?.[0] || null)}
          />

          {ledgerFile ? (
            <div style={{ marginTop: '12px', padding: '6px', background: '#003311', border: '1px solid #00ff66', color: '#aaffaa', fontSize: '12px' }}>
              ✓ Loaded: <strong>{ledgerFile.name}</strong> ({(ledgerFile.size / 1024).toFixed(1)} KB)
            </div>
          ) : (
            <div style={{ marginTop: '12px', color: '#558866', fontSize: '11px' }}>
              [ Click or Drop Ledger CSV Here ]
            </div>
          )}
        </div>

        {/* ZONE 2: P2P Network Telemetry */}
        <div
          style={{
            border: networkFile ? '1px solid #00ff66' : '1px dashed #008833',
            background: networkFile ? 'rgba(0, 40, 18, 0.4)' : 'rgba(0, 15, 8, 0.6)',
            padding: '18px',
            textAlign: 'center',
            cursor: 'pointer',
            borderRadius: '3px',
            transition: 'all 0.2s ease'
          }}
          onClick={() => networkInputRef.current?.click()}
        >
          <div style={{ color: '#00ff66', fontWeight: 'bold', fontSize: '13px', letterSpacing: '1px' }}>
            ZONE 2: OFF-CHAIN P2P NETWORK TELEMETRY
          </div>
          <div style={{ color: '#fff', fontSize: '12px', marginTop: '4px' }}>
            Relay IPs, ASNs, Ports, ISPs &amp; Latency Delays
          </div>
          <div style={{ fontSize: '11px', color: '#77aa88', marginTop: '4px' }}>
            Accepts CSV, JSON, or XML format
          </div>

          <input
            type="file"
            ref={networkInputRef}
            style={{ display: 'none' }}
            onChange={(e) => setNetworkFile(e.target.files?.[0] || null)}
          />

          {networkFile ? (
            <div style={{ marginTop: '12px', padding: '6px', background: '#003311', border: '1px solid #00ff66', color: '#aaffaa', fontSize: '12px' }}>
              ✓ Loaded: <strong>{networkFile.name}</strong> ({(networkFile.size / 1024).toFixed(1)} KB)
            </div>
          ) : (
            <div style={{ marginTop: '12px', color: '#558866', fontSize: '11px' }}>
              [ Click or Drop Network Telemetry CSV Here ]
            </div>
          )}
        </div>
      </div>

      {error && (
        <div style={{
          color: '#ff4455',
          background: 'rgba(40, 0, 10, 0.7)',
          border: '1px solid #ff3344',
          padding: '8px 12px',
          marginBottom: '14px',
          fontSize: '12px',
          borderRadius: '2px'
        }}>
          ⚠️ {error}
        </div>
      )}

      {/* Action Button */}
      <div style={{ textAlign: 'center' }}>
        <button
          onClick={handleCorrelate}
          disabled={isUploading}
          style={{
            background: isUploading ? '#003311' : '#00ff66',
            color: '#030805',
            border: 'none',
            padding: '12px 28px',
            fontSize: '13px',
            fontWeight: 'bold',
            letterSpacing: '1px',
            cursor: isUploading ? 'wait' : 'pointer',
            fontFamily: 'inherit',
            boxShadow: '0 0 15px rgba(0, 255, 102, 0.3)',
            borderRadius: '2px'
          }}
        >
          {isUploading ? '⚡ MERGING DUAL STREAMS & RUNNING V8 ML INFERENCE...' : '[ MERGE DUAL STREAMS & RUN V8 ML INFERENCE ]'}
        </button>
      </div>
    </div>
  );
};
