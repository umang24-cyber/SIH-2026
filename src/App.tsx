import React, { useState, useEffect, useRef, useCallback } from 'react';
import { sound } from './audio/soundEngine';
import { CliOutputRenderer } from './components/CliOutputRenderer';
import { PacmanSplashScreen } from './components/PacmanSplashScreen';
import { LandingPage } from './components/LandingPage';
import { ScrambledAsciiLogo } from './components/ScrambledAsciiLogo';
import { AmbientBinaryRain } from './components/AmbientBinaryRain';
import { CliSpinner } from './components/CliSpinner';
import { api } from './services/api';

interface TerminalEntry {
  id: string;
  command?: string;
  type: 'BANNER' | 'TEXT' | 'ERROR' | 'SUCCESS' | 'HELP' | 'INSPECT' | 'TRACE' | 'LOGS' | 'GRAPH' | 'STATUS' | 'ALERTS' | 'ALERT_DETAIL' | 'TAINT' | 'DOSSIER' | 'DOSSIER_LIST' | 'TOR' | 'INGEST' | 'INGEST_BATCH' | 'TWO_STREAM_UPLOAD' | 'SEARCH' | 'SCENARIOS' | 'BENCHMARK' | 'TELEMETRY' | 'COMMUNITIES' | 'FLOW' | 'ANOMALY' | 'CASE_INIT' | 'CASE_LS' | 'CASE_LIST' | 'CASE_SWITCH';
  content?: any;
}

export function App() {
  const [showSplash, setShowSplash] = useState<boolean>(false);
  const [showLanding, setShowLanding] = useState<boolean>(true);
  const [showTool, setShowTool] = useState<boolean>(false);
  const [inputVal, setInputVal] = useState<string>('');
  const [cursorPos, setCursorPos] = useState<number>(0);
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIdx, setHistoryIdx] = useState<number>(-1);
  const [entries, setEntries] = useState<TerminalEntry[]>([]);
  const [pendingCommand, setPendingCommand] = useState<string | null>(null);
  const [activeCaseName, setActiveCaseName] = useState<string | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const scrollBottomRef = useRef<HTMLDivElement>(null);
  const terminalBodyRef = useRef<HTMLDivElement>(null);
  const lastGraphTimeRef = useRef<number>(0);
  const commandBurstTimestampsRef = useRef<number[]>([]);

  const scrollToBottom = useCallback(() => {
    if (terminalBodyRef.current) {
      terminalBodyRef.current.scrollTop = terminalBodyRef.current.scrollHeight;
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
    const t = setTimeout(scrollToBottom, 30);
    return () => clearTimeout(t);
  }, [entries]);

  useEffect(() => {
    if (showTool) {
      setTimeout(() => inputRef.current?.focus({ preventScroll: true }), 100);
    }
  }, [showTool]);

  useEffect(() => {
    inputRef.current?.focus({ preventScroll: true });

    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      // Don't intercept if user is already typing in an input, textarea, or select
      if (
        document.activeElement instanceof HTMLInputElement ||
        document.activeElement instanceof HTMLTextAreaElement ||
        document.activeElement instanceof HTMLSelectElement
      ) {
        return;
      }

      // Allow terminal shortcuts
      if (e.ctrlKey && (e.key === 'l' || e.key === 'L')) {
        e.preventDefault();
        setEntries([]);
        return;
      }

      // Ignore modifier keys, Escape, F-keys
      if (
        ['Shift', 'Control', 'Alt', 'Meta', 'Escape', 'Tab', 'CapsLock'].includes(e.key) ||
        e.key.startsWith('F')
      ) {
        return;
      }

      // Refocus terminal input seamlessly without jumping scroll
      inputRef.current?.focus({ preventScroll: true });
    };

    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  // Fetch initial active case to sync web prompt
  useEffect(() => {
    api.getActiveCase()
      .then(res => {
        if (res && res.case_name && res.status === 'success') {
          setActiveCaseName(res.case_name);
        } else {
          setActiveCaseName(null);
        }
      })
      .catch(() => setActiveCaseName(null));
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

    let tokens = trimmed.split(/\s+/);
    if (tokens[0].toLowerCase() === 'bitkaun' && tokens.length > 1) {
      tokens = tokens.slice(1);
    }
    const root = tokens[0].toLowerCase();
    const arg1 = tokens[1];
    const arg2 = tokens[2];

    const now = Date.now();

    // General burst command rate limiter (max 8 commands within 2 seconds)
    commandBurstTimestampsRef.current = commandBurstTimestampsRef.current.filter(t => now - t < 2000);
    if (commandBurstTimestampsRef.current.length >= 8) {
      sound.playErrorChirp();
      setEntries(prev => [
        ...prev,
        {
          id: `entry-${Date.now()}`,
          command: trimmed,
          type: 'ERROR',
          content: { message: '[RATE LIMIT] Command burst rate limit exceeded (>8 commands in 2s). Throttling execution to protect engine stability.' }
        }
      ]);
      return;
    }
    commandBurstTimestampsRef.current.push(now);

    sound.playKeyClick();

    // Direct candidate ID evidence lookup (e.g. cand_ransom_...)
    if (root.startsWith('cand_')) {
      sound.playEnterSuccess();
      setPendingCommand(trimmed);
      try {
        const evidence = await api.getAlertEvidence(root);
        setEntries(prev => [
          ...prev,
          {
            id: `entry-${Date.now()}`,
            command: trimmed,
            type: 'ALERT_DETAIL',
            content: evidence
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
            content: { message: `Evidence dossier retrieval failed for candidate '${root}': ${err.message}` }
          }
        ]);
      } finally {
        setPendingCommand(null);
      }
      return;
    }

    switch (root) {
      case 'graph':
      case 'dashboard':
      case 'g':
      case 'nodes':
        {
          const isGraphAlreadyActive = entries.some(e => e.type === 'GRAPH');
          if (isGraphAlreadyActive) {
            // Graph is already active: allow changing scenario if argument provided, or inform user
            if (arg1) {
              sound.playEnterSuccess();
              setEntries(prev => prev.map(e => e.type === 'GRAPH' ? { ...e, content: { scenarioId: arg1 } } : e));
            } else {
              sound.playErrorChirp();
              setEntries(prev => [
                ...prev,
                {
                  id: `entry-${Date.now()}`,
                  command: trimmed,
                  type: 'ERROR',
                  content: {
                    message: '[!] 3D Visual Graph is already active on screen. Click [Close] on graph or enter other commands (alerts, status, tor, inspect, trace).'
                  }
                }
              ]);
            }
            break;
          }

          const GRAPH_COOLDOWN_MS = 1500;
          const timeSinceLast = now - lastGraphTimeRef.current;
          if (timeSinceLast < GRAPH_COOLDOWN_MS) {
            const waitSec = ((GRAPH_COOLDOWN_MS - timeSinceLast) / 1000).toFixed(1);
            sound.playErrorChirp();
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'ERROR',
                content: {
                  message: `[RATE LIMIT] 3D WebGL initialization throttled. Please wait ${waitSec}s before launching another 3D graph to protect WebGL GPU context.`
                }
              }
            ]);
            break;
          }
          lastGraphTimeRef.current = now;

          sound.playEnterSuccess();
          // ENFORCE SINGLETON 3D GRAPH: Close any prior active GRAPH canvas to prevent multi-WebGL context GPU crashes
          setEntries(prev => {
            const nonGraph = prev.filter(e => e.type !== 'GRAPH');
            return [
              ...nonGraph,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'GRAPH',
                content: { scenarioId: arg1 || 'normal_00002' }
              }
            ];
          });

          if (tokens.includes('--save')) {
            const scId = (arg1 && !arg1.startsWith('-')) ? arg1 : 'normal_00002';
            api.getGraph(scId)
              .then(g => api.saveCaseArtifact({ command_name: 'graph', identifier: scId, data: g }))
              .then(res => setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'SUCCESS', content: `[✓] Saved graph artifact to active case: ${res.relative_path || res.filename}` }]))
              .catch(() => setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'ERROR', content: { message: `[X] No active case — run 'init <name>' first` } }]));
          }
        }
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
        setPendingCommand(trimmed);
        try {
          // Check if numeric txid or address
          const isNumeric = /^\d+$/.test(arg1);
          if (isNumeric) {
            const tx = await api.getTransaction(arg1);
            let risk = 10;
            if (tx.scenario_id) {
              try {
                const analysis = await api.getIngestScenarioAnalysis(tx.scenario_id);
                if (analysis.analysis_status === 'AVAILABLE' && typeof analysis.risk_score === 'number') {
                  risk = Math.round(analysis.risk_score * 100);
                } else if (analysis.is_illicit) {
                  risk = 85;
                }
              } catch {
                const isIllicit = !tx.scenario_id.toLowerCase().startsWith('licit') && !tx.scenario_id.toLowerCase().startsWith('normal');
                risk = isIllicit ? 85 : 10;
              }
            }

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
                    riskScore: risk,
                    clusterId: tx.scenario_id,
                    balanceBtc: tx.output_amounts ? tx.output_amounts.reduce((a: number, b: number) => a + b, 0) : 0,
                    txCount: 1,
                    firstSeen: tx.timestamp,
                    lastSeen: tx.timestamp,
                    tags: [tx.script_type, tx.network?.node_type || 'standard_relay'],
                    flags: tx.network?.node_type?.includes('tor') ? ['TOR_EXIT_NODE'] : []
                  }
                }
              }
            ]);

            if (tokens.includes('--save')) {
              api.saveCaseArtifact({ command_name: 'inspect', identifier: `tx_${arg1}`, data: tx })
                .then(res => setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'SUCCESS', content: `[✓] Saved inspect artifact to active case: ${res.relative_path || res.filename}` }]))
                .catch(() => setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'ERROR', content: { message: `[X] No active case — run 'init <name>' first` } }]));
            }
          } else {
            // Check whether arg1 is a scenario cluster or a Bitcoin address
            let isScenario = false;
            let scenarioData: any = null;
            const looksLikeAddress = /^(1|3|bc1|0x)[a-zA-HJ-NP-Z0-9]{15,62}$/i.test(arg1);

            if (!looksLikeAddress) {
              try {
                scenarioData = await api.getScenario(arg1);
                isScenario = !!scenarioData;
              } catch {}
            }

            if (isScenario && scenarioData) {
              let risk = Math.round(scenarioData.infrastructure_risk_score || 0);
              let typology = scenarioData.dominant_typology || 'scenario_cluster';
              let analysis: any = null;
              try {
                analysis = await api.getIngestScenarioAnalysis(arg1);
                if (analysis.analysis_status === 'AVAILABLE' && typeof analysis.risk_score === 'number') {
                  risk = Math.round(analysis.risk_score * 100);
                } else if (analysis.is_illicit) {
                  risk = 85;
                }
                if (analysis.predicted_typology) {
                  typology = analysis.predicted_typology;
                }
              } catch {}

              const topWallets = scenarioData.top_hub_wallets?.map((h: any) => h.address) || [];
              const memberTxids = scenarioData.member_txids || [];

              setEntries(prev => [
                ...prev,
                {
                  id: `entry-${Date.now()}`,
                  command: trimmed,
                  type: 'INSPECT',
                  content: {
                    id: `SCENARIO:${scenarioData.scenario_id}`,
                    raw: scenarioData,
                    node: {
                      id: `SCENARIO:${scenarioData.scenario_id}`,
                      label: `Scenario Cluster: ${scenarioData.scenario_id}`,
                      type: 'SCENARIO',
                      riskScore: risk,
                      clusterId: scenarioData.scenario_id,
                      balanceBtc: scenarioData.total_input_volume_btc || 0,
                      txCount: scenarioData.transaction_count || memberTxids.length,
                      firstSeen: scenarioData.time_window?.start || 'N/A',
                      lastSeen: scenarioData.time_window?.end || 'N/A',
                      tags: [typology, ...(scenarioData.origin_countries || [])],
                      flags: risk >= 75 ? ['CRITICAL_THREAT_CLUSTER', 'SUSPICIOUS_ROUTING'] : ['INDEXED_SCENARIO'],
                      isLicitExchange: typology.toLowerCase().includes('licit')
                    },
                    data: {
                      scenario: scenarioData,
                      analysis: analysis,
                      scenario_id: scenarioData.scenario_id,
                      dominant_typology: typology,
                      member_txids: memberTxids,
                      top_hub_wallets: scenarioData.top_hub_wallets || [],
                      input_addresses: topWallets,
                      output_addresses: topWallets.slice(1),
                      input_amounts: topWallets.map(() => scenarioData.total_input_volume_btc || 0),
                      fee_btc: scenarioData.total_fees_btc || 0,
                      network: {
                        node_type: Object.keys(scenarioData.infrastructure_breakdown || {})[0] || 'mixed',
                        country_code: scenarioData.origin_countries?.join(', ') || 'US',
                        asn: scenarioData.origin_asns?.join(', ') || 'N/A',
                        isp: 'Scenario Telemetry Fabric',
                        propagation_delta_ms: scenarioData.average_propagation_delta_ms || 0
                      }
                    }
                  }
                }
              ]);
            } else {
              // Address path with scenario fallback if entity is not found
              let entity: any = null;
              try {
                entity = await api.getEntity(arg1);
              } catch (entityErr: any) {
                try {
                  const fallbackSc = await api.getScenario(arg1);
                  if (fallbackSc) {
                    scenarioData = fallbackSc;
                  }
                } catch {}
                if (!scenarioData) {
                  throw entityErr;
                }
              }

              if (scenarioData) {
                let risk = Math.round(scenarioData.infrastructure_risk_score || 0);
                let typology = scenarioData.dominant_typology || 'scenario_cluster';
                let analysis: any = null;
                try {
                  analysis = await api.getIngestScenarioAnalysis(arg1);
                  if (analysis.analysis_status === 'AVAILABLE' && typeof analysis.risk_score === 'number') {
                    risk = Math.round(analysis.risk_score * 100);
                  }
                  if (analysis.predicted_typology) {
                    typology = analysis.predicted_typology;
                  }
                } catch {}

                const topWallets = scenarioData.top_hub_wallets?.map((h: any) => h.address) || [];
                const memberTxids = scenarioData.member_txids || [];

                setEntries(prev => [
                  ...prev,
                  {
                    id: `entry-${Date.now()}`,
                    command: trimmed,
                    type: 'INSPECT',
                    content: {
                      id: `SCENARIO:${scenarioData.scenario_id}`,
                      raw: scenarioData,
                      node: {
                        id: `SCENARIO:${scenarioData.scenario_id}`,
                        label: `Scenario Cluster: ${scenarioData.scenario_id}`,
                        type: 'SCENARIO',
                        riskScore: risk,
                        clusterId: scenarioData.scenario_id,
                        balanceBtc: scenarioData.total_input_volume_btc || 0,
                        txCount: scenarioData.transaction_count || memberTxids.length,
                        firstSeen: scenarioData.time_window?.start || 'N/A',
                        lastSeen: scenarioData.time_window?.end || 'N/A',
                        tags: [typology, ...(scenarioData.origin_countries || [])],
                        flags: risk >= 75 ? ['CRITICAL_THREAT_CLUSTER', 'SUSPICIOUS_ROUTING'] : ['INDEXED_SCENARIO'],
                        isLicitExchange: typology.toLowerCase().includes('licit')
                      },
                      data: {
                        scenario: scenarioData,
                        analysis: analysis,
                        scenario_id: scenarioData.scenario_id,
                        dominant_typology: typology,
                        member_txids: memberTxids,
                        top_hub_wallets: scenarioData.top_hub_wallets || [],
                        input_addresses: topWallets,
                        output_addresses: topWallets.slice(1),
                        input_amounts: topWallets.map(() => scenarioData.total_input_volume_btc || 0),
                        fee_btc: scenarioData.total_fees_btc || 0,
                        network: {
                          node_type: Object.keys(scenarioData.infrastructure_breakdown || {})[0] || 'mixed',
                          country_code: scenarioData.origin_countries?.join(', ') || 'US',
                          asn: scenarioData.origin_asns?.join(', ') || 'N/A',
                          isp: 'Scenario Telemetry Fabric',
                          propagation_delta_ms: scenarioData.average_propagation_delta_ms || 0
                        }
                      }
                    }
                  }
                ]);

                if (tokens.includes('--save')) {
                  api.saveCaseArtifact({ command_name: 'inspect', identifier: `scenario_${scenarioData.scenario_id}`, data: scenarioData })
                    .then(res => setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'SUCCESS', content: `[✓] Saved inspect artifact to active case: ${res.relative_path || res.filename}` }]))
                    .catch(() => setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'ERROR', content: { message: `[X] No active case — run 'init <name>' first` } }]));
                }
              } else {
                let clusterId = 'UNCLUSTERED';
                try {
                  const cl = await api.getEntityCluster(arg1);
                  clusterId = cl.cluster_id;
                } catch {}

                let risk = entity.is_licit_exchange ? 5 : 15;
                if (entity.associated_scenarios && entity.associated_scenarios.length > 0) {
                  const sc = entity.associated_scenarios[0];
                  try {
                    const analysis = await api.getIngestScenarioAnalysis(sc);
                    if (analysis.analysis_status === 'AVAILABLE' && typeof analysis.risk_score === 'number') {
                      risk = Math.round(analysis.risk_score * 100);
                    } else if (analysis.is_illicit) {
                      risk = 85;
                    }
                  } catch {
                    const isIllicit = entity.associated_scenarios.some((s: string) => !s.toLowerCase().startsWith('licit') && !s.toLowerCase().startsWith('normal'));
                    risk = isIllicit ? 85 : 15;
                  }
                }

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
                        riskScore: risk,
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

                if (tokens.includes('--save')) {
                  api.saveCaseArtifact({ command_name: 'inspect', identifier: `entity_${arg1}`, data: entity })
                    .then(res => setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'SUCCESS', content: `[✓] Saved inspect artifact to active case: ${res.relative_path || res.filename}` }]))
                    .catch(() => setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'ERROR', content: { message: `[X] No active case — run 'init <name>' first` } }]));
                }
              }
            }
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
        } finally {
          setPendingCommand(null);
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
        setPendingCommand(trimmed);
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

          if (tokens.includes('--save')) {
            api.saveCaseArtifact({ command_name: 'trace', identifier: `${arg1}_to_${arg2}`, data: traceResult })
              .then(res => setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'SUCCESS', content: `[✓] Saved trace artifact to active case: ${res.relative_path || res.filename}` }]))
              .catch(() => setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'ERROR', content: { message: `[X] No active case — run 'init <name>' first` } }]));
          }
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
        } finally {
          setPendingCommand(null);
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
              content: { message: "Usage: taint <seed_address> (e.g. 'taint 18hvz1KnqUjLRr3KHifSbMDi6m')" }
            }
          ]);
          return;
        }
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
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
        } finally {
          setPendingCommand(null);
        }
        break;

      case 'alerts':
      case 'alert':
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
        try {
          // Check for detail inspection flags: alerts --detail <id>, alerts -d <id>, alerts cand_...
          let targetCandidateId: string | null = null;
          if (arg1 === '--detail' || arg1 === '-d') {
            targetCandidateId = arg2 || null;
          } else if (arg1 && arg1.startsWith('cand_')) {
            targetCandidateId = arg1;
          }

          if (targetCandidateId) {
            const evidence = await api.getAlertEvidence(targetCandidateId);
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'ALERT_DETAIL',
                content: evidence
              }
            ]);

            if (tokens.includes('--save')) {
              api.saveCaseArtifact({ command_name: 'alerts', identifier: targetCandidateId, data: evidence, subfolder: 'dossiers' })
                .then(res => setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'SUCCESS', content: `[✓] Saved alert dossier to active case: ${res.relative_path || res.filename}` }]))
                .catch(() => setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'ERROR', content: { message: `[X] No active case — run 'init <name>' first` } }]));
            }
          } else {
            // Options parsing: limit, typology, min_confidence
            let limit = 25;
            let patternType: string | undefined = undefined;
            let minConfidence = 0.50;

            for (let i = 1; i < tokens.length; i++) {
              const t = tokens[i].toLowerCase();
              if ((t === '--limit' || t === '-l') && tokens[i + 1]) {
                const parsed = parseInt(tokens[i + 1], 10);
                if (!isNaN(parsed) && parsed > 0) limit = parsed;
              } else if (/^\d+$/.test(t) && i === 1) {
                limit = parseInt(t, 10);
              } else if ((t === '--pattern' || t === '-p' || t === '--typology' || t === '-t') && tokens[i + 1]) {
                patternType = tokens[i + 1];
              } else if ((t === '--confidence' || t === '-c' || t === '--min-confidence') && tokens[i + 1]) {
                const parsedConf = parseFloat(tokens[i + 1]);
                if (!isNaN(parsedConf)) minConfidence = parsedConf;
              }
            }

            const alertsRes = await api.getAlerts(minConfidence, limit, patternType);
            // Sort alerts descending by risk_score or binary_confidence like Python CLI
            if (alertsRes && Array.isArray(alertsRes.alerts)) {
              alertsRes.alerts = [...alertsRes.alerts].sort((a, b) => {
                const scoreA = Number(a.risk_score ?? a.binary_confidence ?? 0);
                const scoreB = Number(b.risk_score ?? b.binary_confidence ?? 0);
                return scoreB - scoreA;
              });
            }

            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'ALERTS',
                content: alertsRes
              }
            ]);

            if (tokens.includes('--save')) {
              api.saveCaseArtifact({ command_name: 'alerts', identifier: 'queue', data: alertsRes })
                .then(res => setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'SUCCESS', content: `[✓] Saved alerts artifact to active case: ${res.relative_path || res.filename}` }]))
                .catch(() => setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'ERROR', content: { message: `[X] No active case — run 'init <name>' first` } }]));
            }
          }
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
        } finally {
          setPendingCommand(null);
        }
        break;

      case 'dossier':
      case 'dossiers':
      case 'report':
        if (arg1 === 'list') {
          sound.playEnterSuccess();
          setPendingCommand(trimmed);
          try {
            const savedList = await api.listSavedDossiers();
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'DOSSIER_LIST',
                content: savedList
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
                content: { message: `Failed to retrieve saved dossiers: ${err.message}` }
              }
            ]);
          } finally {
            setPendingCommand(null);
          }
          return;
        }

        if (!arg1) {
          sound.playErrorChirp();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'ERROR',
              content: { message: "Usage: dossier <txid|scenario_id> or 'dossier list' (e.g. 'dossier 999182736', 'dossier list')" }
            }
          ]);
          return;
        }
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
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

          if (tokens.includes('--save')) {
            api.saveCaseArtifact({ command_name: 'dossier', identifier: arg1, data: dossierRes, subfolder: 'dossiers' })
              .then(res => setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'SUCCESS', content: `[✓] Saved dossier artifact to active case: ${res.relative_path || res.filename}` }]))
              .catch(() => setEntries(prev => [...prev, { id: `entry-${Date.now()}`, type: 'ERROR', content: { message: `[X] No active case — run 'init <name>' first` } }]));
          }
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
        } finally {
          setPendingCommand(null);
        }
        break;

      case 'tor':
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
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
        } finally {
          setPendingCommand(null);
        }
        break;

      case 'logs':
      case 'log':
      case 'stream':
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
        try {
          const streamLimit = Math.min(Math.max(parseInt(arg1, 10) || 15, 1), 100);
          const batch = await api.getStreamBatch(streamLimit);
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'LOGS',
              content: batch
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
              content: { message: `Stream telemetry failed: ${err.message}` }
            }
          ]);
        } finally {
          setPendingCommand(null);
        }
        break;

      case 'init':
        if (!arg1) {
          sound.playErrorChirp();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'ERROR',
              content: { message: "Usage: init <case_name> (e.g. 'init operation_black_lotus' or 'init test1')" }
            }
          ]);
          return;
        }
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
        try {
          const caseName = tokens.slice(1).join('_').replace(/["']/g, '');
          const res = await api.initCase(caseName);
          if (res && res.case_name) {
            setActiveCaseName(res.case_name);
          }
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'CASE_INIT',
              content: res
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
              content: { message: `Failed to initialize case: ${err.message}` }
            }
          ]);
        } finally {
          setPendingCommand(null);
        }
        break;

      case 'cd':
      case 'case':
      case 'checkout':
      case 'use':
      case 'cases':
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
        try {
          if (root === 'cases' || ((root === 'cd' || root === 'case') && (!arg1 || arg1 === 'ls'))) {
            const listRes = await api.listCases();
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'CASE_LIST',
                content: listRes
              }
            ]);
            break;
          }

          const target = arg1?.replace(/["']/g, '').trim();
          if (['..', '~', '/', 'main', 'none', 'unset', 'exit'].includes(target)) {
            await api.setActiveCase('');
            setActiveCaseName(null);
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'CASE_SWITCH',
                content: { case_name: null }
              }
            ]);
            break;
          }

          await api.setActiveCase(target);
          setActiveCaseName(target);
          const activeDetails = await api.getActiveCase().catch(() => null);
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'CASE_SWITCH',
              content: {
                case_name: target,
                location: activeDetails?.location,
                reports_count: activeDetails?.counts?.reports ?? 0,
                dossiers_count: activeDetails?.counts?.dossiers ?? 0,
                evidence_count: activeDetails?.counts?.evidence ?? 0
              }
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
              content: { message: `Case '${arg1}' not found. Type 'cases' to list existing cases, or 'init ${arg1}' to create it.` }
            }
          ]);
        } finally {
          setPendingCommand(null);
        }
        break;

      case 'ls':
      case 'list':
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
        try {
          const res = await api.getCaseLs(arg1 || 'active');
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'CASE_LS',
              content: res
            }
          ]);
        } catch (err: any) {
          sound.playErrorChirp();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'CASE_LS',
              content: {
                status: 'no_case',
                message: "No active forensic case directory found. Run 'init <case_name>' to create an active case."
              }
            }
          ]);
        } finally {
          setPendingCommand(null);
        }
        break;

      case 'status':
      case 'sys':
      case 'health':
        sound.playEnterSuccess();
        setPendingCommand(trimmed);
        try {
          const [health, activeCase] = await Promise.all([
            api.getHealth(),
            api.getActiveCase().catch(() => null)
          ]);
          if (activeCase && activeCase.case_name && activeCase.status === 'success') {
            setActiveCaseName(activeCase.case_name);
          } else {
            setActiveCaseName(null);
          }
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'STATUS',
              content: { ...health, active_case: activeCase }
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
        } finally {
          setPendingCommand(null);
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

      case 'ingest':
        if (!arg1 || arg1 === 'help') {
          sound.playEnterSuccess();
          setEntries(prev => [
            ...prev,
            {
              id: `entry-${Date.now()}`,
              command: trimmed,
              type: 'TEXT',
              content: {
                message: [
                  '================================================================================',
                  ' BITKAUN DYNAMIC TRANSACTION INGESTION & AI/ML CORRELATION ENGINE',
                  '================================================================================',
                  ' Inject live Bitcoin transactions directly into the in-memory graph without restart.',
                  ' Ingested transactions are automatically indexed, correlated with network telemetry,',
                  ' and scored by the XGBoost & Isolation Forest inference pipeline with live SHAP.',
                  '',
                  ' USAGE:',
                  '   ingest sample [type]      - Ingest a realistic synthetic scenario sample',
                  '                               Types: ransomware | peeling_chain | mixing | licit',
                  '   ingest <raw_json>          - Ingest custom JSON transaction payload',
                  '   upload                     - Batch ingest CSV, JSON, or XML ledger files',
                  '',
                  ' QUICK PRESETS (Click to Run):',
                  '   [ingest sample ransomware]    - Live Ransomware extortion split & Tor relay',
                  '   [ingest sample peeling_chain] - Rapid Peel Chain UTXO wash with change address',
                  '   [ingest sample mixing]        - CoinJoin mixer equal-output high-fanout pattern',
                  '   [ingest sample licit]         - Clean merchant / licensed exchange transaction',
                  '================================================================================'
                ].join('\n')
              }
            }
          ]);
          return;
        }

        if (arg1 === 'sample') {
          const sampleType = arg2 || 'ransomware';
          sound.playEnterSuccess();
          setPendingCommand(trimmed);
          try {
            const sampleData = await api.getIngestSample(sampleType);
            const txToIngest = sampleData.sample_transaction || sampleData;
            const ingestRes = await api.ingestTransaction(txToIngest);
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'INGEST',
                content: ingestRes
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
                content: { message: `Sample ingestion failed: ${err.message}` }
              }
            ]);
          } finally {
            setPendingCommand(null);
          }
          return;
        }

        // Handle raw JSON ingestion
        {
          const jsonStr = trimmed.slice(root.length).trim();
          let parsedTx: any;
          try {
            parsedTx = JSON.parse(jsonStr);
          } catch (e: any) {
            sound.playErrorChirp();
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'ERROR',
                content: {
                  message: `Invalid JSON syntax for transaction ingestion: ${e.message}\nUsage: ingest {"inputs": ["1..."], "outputs": [{"address": "1...", "amount": 1.5}]}`
                }
              }
            ]);
            return;
          }

          sound.playEnterSuccess();
          setPendingCommand(trimmed);
          try {
            const ingestRes = await api.ingestTransaction(parsedTx);
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'INGEST',
                content: ingestRes
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
                content: { message: `Transaction ingestion failed: ${err.message}` }
              }
            ]);
          } finally {
            setPendingCommand(null);
          }
        }
        break;

      case 'upload':
      case 'correlate':
      case 'dualstream':
        sound.playEnterSuccess();
        setEntries(prev => [
          ...prev,
          {
            id: `entry-${Date.now()}`,
            command: trimmed,
            type: 'TWO_STREAM_UPLOAD',
          }
        ]);
        break;

      case 'search':
      case 'find':
      case 'query':
        {
          const query = trimmed.slice(root.length).trim();
          if (!query) {
            sound.playErrorChirp();
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'ERROR',
                content: { message: "Usage: search <txid | address | IP | ASN | scenario_id>\nExamples:\n  search 881920041\n  search 1PeelHeadWallet0001\n  search AS49981\n  search peeling_chain_04651" }
              }
            ]);
            return;
          }
          sound.playEnterSuccess();
          setPendingCommand(trimmed);
          try {
            const res = await api.search(query);
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'SEARCH',
                content: res
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
                content: { message: `Forensic search failed: ${err.message}` }
              }
            ]);
          } finally {
            setPendingCommand(null);
          }
        }
        break;

      case 'scenarios':
      case 'clusters':
        {
          sound.playEnterSuccess();
          setPendingCommand(trimmed);
          let prefix: string | undefined = undefined;
          let page = 1;

          if (arg1 && isNaN(Number(arg1))) {
            prefix = arg1;
            if (arg2 && !isNaN(Number(arg2))) {
              page = Math.max(1, parseInt(arg2, 10));
            }
          } else if (arg1 && !isNaN(Number(arg1))) {
            page = Math.max(1, parseInt(arg1, 10));
          }

          try {
            const res = await api.getScenarios(prefix, page, 20);
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'SCENARIOS',
                content: { ...res, prefix }
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
                content: { message: `Scenario directory retrieval failed: ${err.message}` }
              }
            ]);
          } finally {
            setPendingCommand(null);
          }
        }
        break;

      case 'benchmark':
      case 'eval':
      case 'metrics':
      case 'accuracy':
        {
          sound.playEnterSuccess();
          setPendingCommand(trimmed);
          try {
            const res = await api.getBenchmark();
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'BENCHMARK',
                content: res
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
                content: { message: `Benchmark evaluation failed: ${err.message}` }
              }
            ]);
          } finally {
            setPendingCommand(null);
          }
        }
        break;

      case 'telemetry':
      case 'stats':
      case 'p2p':
        {
          sound.playEnterSuccess();
          setPendingCommand(trimmed);
          try {
            const res = await api.getStatsTelemetry();
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'TELEMETRY',
                content: res
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
                content: { message: `Telemetry statistics retrieval failed: ${err.message}` }
              }
            ]);
          } finally {
            setPendingCommand(null);
          }
        }
        break;

      case 'communities':
      case 'community':
      case 'syndicates':
        {
          const targetScenario = arg1 || 'peeling_chain_04651';
          sound.playEnterSuccess();
          setPendingCommand(trimmed);
          try {
            const res = await api.getGraphCommunities(targetScenario);
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'COMMUNITIES',
                content: { ...res, scenario_id: targetScenario }
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
                content: { message: `Community detection failed for '${targetScenario}': ${err.message}` }
              }
            ]);
          } finally {
            setPendingCommand(null);
          }
        }
        break;

      case 'flow':
      case 'decompose':
        {
          if (!arg1) {
            sound.playErrorChirp();
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'ERROR',
                content: { message: "Usage: flow <txid> (e.g. 'flow 881920041')" }
              }
            ]);
            return;
          }
          const txidNum = parseInt(arg1, 10);
          if (isNaN(txidNum)) {
            sound.playErrorChirp();
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'ERROR',
                content: { message: `Invalid TxID '${arg1}'. Flow command requires a numeric transaction ID.` }
              }
            ]);
            return;
          }
          sound.playEnterSuccess();
          setPendingCommand(trimmed);
          try {
            const res = await api.getTransactionFlow(txidNum);
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'FLOW',
                content: res
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
                content: { message: `Flow decomposition failed for TX #${txidNum}: ${err.message}` }
              }
            ]);
          } finally {
            setPendingCommand(null);
          }
        }
        break;

      case 'anomaly':
      case 'unusual':
        {
          const targetScenario = arg1 || 'peeling_chain_04651';
          sound.playEnterSuccess();
          setPendingCommand(trimmed);
          try {
            const res = await api.getAnomalyScore(targetScenario);
            setEntries(prev => [
              ...prev,
              {
                id: `entry-${Date.now()}`,
                command: trimmed,
                type: 'ANOMALY',
                content: res
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
                content: { message: `Isolation Forest anomaly scoring failed for '${targetScenario}': ${err.message}` }
              }
            ]);
          } finally {
            setPendingCommand(null);
          }
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

  const syncCursorPos = (target: HTMLInputElement | null) => {
    if (!target) return;
    const pos = target.selectionStart ?? target.value.length;
    setCursorPos(pos);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== 'Enter' && e.key !== 'Tab') {
      sound.playKeyClick();
    }

    if (e.key === 'Enter') {
      e.preventDefault();
      handleRunCommand(inputVal);
      setInputVal('');
      setCursorPos(0);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length > 0) {
        const nextIdx = Math.min(historyIdx + 1, commandHistory.length - 1);
        setHistoryIdx(nextIdx);
        const val = commandHistory[nextIdx];
        setInputVal(val);
        setCursorPos(val.length);
        setTimeout(() => {
          if (inputRef.current) {
            inputRef.current.setSelectionRange(val.length, val.length);
          }
        }, 0);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIdx > 0) {
        const prevIdx = historyIdx - 1;
        setHistoryIdx(prevIdx);
        const val = commandHistory[prevIdx];
        setInputVal(val);
        setCursorPos(val.length);
        setTimeout(() => {
          if (inputRef.current) {
            inputRef.current.setSelectionRange(val.length, val.length);
          }
        }, 0);
      } else if (historyIdx === 0) {
        setHistoryIdx(-1);
        setInputVal('');
        setCursorPos(0);
      }
    } else if (e.key === 'Tab') {
      e.preventDefault();
      const trimmed = inputVal.trim();
      if (!trimmed) return;
      const allCmds = ['graph', 'inspect', 'trace', 'taint', 'alerts', 'dossier', 'tor', 'ingest', 'upload', 'status', 'help', 'clear', 'sound', 'reboot'];
      const match = allCmds.find(c => c.startsWith(trimmed.toLowerCase()));
      if (match) {
        const completed = match + ' ';
        setInputVal(completed);
        setCursorPos(completed.length);
        setTimeout(() => {
          if (inputRef.current) {
            inputRef.current.setSelectionRange(completed.length, completed.length);
          }
        }, 0);
      }
    } else if (e.ctrlKey && (e.key === 'l' || e.key === 'L')) {
      e.preventDefault();
      setEntries([]);
    } else if (['ArrowLeft', 'ArrowRight', 'Home', 'End', 'Backspace', 'Delete'].includes(e.key)) {
      requestAnimationFrame(() => syncCursorPos(inputRef.current));
    }
  };

  const safeCursorPos = Math.max(0, Math.min(cursorPos, inputVal.length));
  const textBefore = inputVal.slice(0, safeCursorPos);
  const charAtCursor = inputVal.slice(safeCursorPos, safeCursorPos + 1);
  const textAfter = inputVal.slice(safeCursorPos + 1);

  const handleTerminalWindowClick = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement | null;
    if (!target) return;
    // Don't steal focus if clicking interactive elements inside widgets
    if (
      target.closest(
        'button, a, input, select, textarea, [role="button"], .cmd-tag, .cmd-clickable, .hud-pill, .window-ctrl-btn, .node-details-card'
      )
    ) {
      return;
    }
    inputRef.current?.focus({ preventScroll: true });
  };

  const enterCLI = () => {
    setShowSplash(true);
  };

  const handleSplashEntranceComplete = useCallback(() => {
    setShowLanding(false);
  }, []);

  const handleSplashComplete = useCallback(() => {
    setShowLanding(false);
    setShowSplash(false);
    setShowTool(true);
  }, []);

  return (
    <div className="terminal-window" onClick={handleTerminalWindowClick}>
      <AmbientBinaryRain />

      {showSplash && (
        <PacmanSplashScreen
          autoStart
          entranceFromLanding
          onEntranceComplete={handleSplashEntranceComplete}
          onComplete={handleSplashComplete}
        />
      )}

      {showLanding && (
        <LandingPage onEnterCLI={enterCLI} isExiting={showSplash} />
      )}

      {showTool && !showSplash && !showLanding && (
        <>
        <div className="terminal-titlebar">
        <div className="window-dots">
          <span className="window-dot dot-red" />
          <span className="window-dot dot-yellow" />
          <span className="window-dot dot-green" />
        </div>
        <div style={{ fontWeight: 500 }}>bitkaun@investigation{activeCaseName ? ` (${activeCaseName})` : ''}: ~ (bash)</div>
        <div style={{ fontSize: '12px', color: '#555555' }}>x86_64 tty1 [FASTAPI LINKED]</div>
      </div>

      {/* Terminal Content Buffer */}
      <div ref={terminalBodyRef} className="terminal-body">
        {/* Permanent Welcome Header & Available Commands */}
        <div className="output-block" style={{ borderBottom: '1px solid var(--border-mid)', paddingBottom: '14px', marginBottom: '8px' }}>
          <ScrambledAsciiLogo active={!showSplash} />

          <div style={{ color: 'var(--fg-white)', fontSize: '15px', fontWeight: 600, marginBottom: '4px' }}>
            Welcome to BitKaun (Version 8.0.0 · Dual-Stream Forensic Engine)
          </div>
          <div style={{ color: 'var(--fg-muted)', marginBottom: '16px', fontSize: '14px' }}>
            Bitcoin Cross-Layer AML Forensics &amp; Dual-Stream Telemetry Correlation.
            <br />
            Type <span className="cmd-tag" onClick={() => handleRunCommand('help')}>'help'</span> to see all forensic commands.
          </div>

          <div style={{ color: 'var(--fg-primary)', fontWeight: 600, marginBottom: '6px' }}>
            Interactive Commands (Click to Run):
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '6px', marginBottom: '8px', color: 'var(--fg-text)', fontSize: '14px' }}>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('status')}>[status]</span>
              <span className="cmd-desc"> - Memory engine diagnostics</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('graph')}>[graph]</span>
              <span className="cmd-desc"> - 3D WebGL visual graph explorer</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('alerts')}>[alerts]</span>
              <span className="cmd-desc"> - Typology alert feed & SHAP</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('tor')}>[tor]</span>
              <span className="cmd-desc"> - Tor timing entropy profiler</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('ingest sample ransomware')}>[ingest sample]</span>
              <span className="cmd-desc"> - Live inject custom flow & ML</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('correlate')}>[correlate]</span>
              <span className="cmd-desc"> - Dual-stream Ledger + P2P correlation</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('help')}>[help]</span>
              <span className="cmd-desc"> - Detailed command manual</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('cases')}>[cases]</span>
              <span className="cmd-desc"> - List & switch active cases</span>
            </div>
            <div>
              <span className="cmd-tag" onClick={() => handleRunCommand('clear')}>[clear]</span>
              <span className="cmd-desc"> - Clear screen (Ctrl+L)</span>
            </div>
          </div>
        </div>

        {/* Dynamic Command Outputs */}
        {entries.map(entry => (
          <div key={entry.id}>
            {entry.command !== undefined && (
              <div className="prompt-line" style={{ marginBottom: '4px' }}>
                <span className="prompt-prefix">bitkaun@investigation{activeCaseName ? ` (${activeCaseName})` : ''}</span>
                <span className="prompt-char">:$</span>
                <span style={{ color: 'var(--fg-white)', wordBreak: 'break-all', overflowWrap: 'anywhere' }}>{entry.command}</span>
              </div>
            )}

            <CliOutputRenderer
              entry={entry}
              onRunCommand={handleRunCommand}
              onScrollRequested={scrollToBottom}
              onCloseEntry={(id) => setEntries(prev => prev.filter(e => e.id !== id))}
            />
          </div>
        ))}

        {/* Active Command Execution Spinner */}
        {pendingCommand && (
          <div style={{ margin: '8px 0', padding: '4px 0', color: '#00ff66', fontFamily: 'monospace' }}>
            <CliSpinner label={`EXECUTING COMMAND: [${pendingCommand}] ...`} />
          </div>
        )}

        {/* Current Active Input Prompt */}
        <div className="prompt-line">
          <span className="prompt-prefix">bitkaun@investigation{activeCaseName ? ` (${activeCaseName})` : ''}</span>
          <span className="prompt-char">:$</span>
          <div className="input-cursor-wrapper">
            <span className="typed-text">{textBefore}</span>
            <span key={safeCursorPos} className="cli-cursor">
              {charAtCursor || '\u00A0'}
            </span>
            <span className="typed-text">{textAfter}</span>
            <input
              ref={inputRef}
              type="text"
              className="terminal-real-input"
              value={inputVal}
              onChange={e => {
                setInputVal(e.target.value);
                setCursorPos(e.target.selectionStart ?? e.target.value.length);
              }}
              onKeyDown={handleKeyDown}
              onKeyUp={e => syncCursorPos(e.currentTarget)}
              onClick={e => syncCursorPos(e.currentTarget)}
              onSelect={e => syncCursorPos(e.currentTarget)}
              onFocus={e => syncCursorPos(e.currentTarget)}
              autoFocus
              spellCheck={false}
              autoComplete="off"
            />
          </div>
        </div>

        <div ref={scrollBottomRef} />
      </div>
    </>
    )}
    </div>
  );
}

export default App;
