export interface GraphNode {
  id: string;
  type: 'Wallet' | 'Transaction' | 'IP';
  label: string;
  x: number; // percentage coordinate 0-100
  y: number; // percentage coordinate 0-100
  properties: {
    address?: string;
    is_licit_exchange?: boolean;
    balance_btc?: number;
    txid?: number;
    timestamp?: string;
    fee_btc?: number;
    script_type?: string;
    relay_ip?: string;
    country_code?: string;
    asn?: string;
    isp?: string;
    node_type?: 'residential' | 'bulletproof_host' | 'tor_exit' | 'vpn';
    relay_port?: number;
    propagation_delta_ms?: number;
  };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: 'SENT' | 'RECEIVED' | 'BROADCAST';
  amount_btc?: number;
  relay_timestamp?: string;
  relay_port?: number;
  user_agent?: string;
}

export interface ShapAttribution {
  feature_name: string;
  value: number | string;
  shap_value: number;
  direction: 'RISK_INCREASING' | 'RISK_DECREASING';
}

export interface ForensicAlert {
  candidate_id: string;
  scenario_id: string;
  predicted_pattern_type: 'peeling_chain' | 'layering' | 'mixing' | 'ransomware';
  binary_confidence: number;
  typology_confidence: number;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM';
  explanation: string;
  primary_wallet: string;
  member_txids: number[];
  member_wallets: string[];
  detected_at: string;
}

export interface ForensicScenario {
  id: string;
  name: string;
  pattern_type: 'peeling_chain' | 'layering' | 'mixing' | 'ransomware';
  confidence: number;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM';
  summary: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  alerts: ForensicAlert[];
  shap_attributions: ShapAttribution[];
  telemetry: {
    origin_ips: string[];
    origin_asns: string[];
    countries: string[];
    infrastructure_distribution: Record<string, number>;
  };
}

export const FORENSIC_SCENARIOS: Record<string, ForensicScenario> = {
  peel_001: {
    id: 'peel_001',
    name: 'Peeling Chain Alpha (Heist Dispersal)',
    pattern_type: 'peeling_chain',
    confidence: 0.942,
    severity: 'CRITICAL',
    summary: 'Sequential 1-in-2-out transactions peeling small outputs (avg 0.05 BTC) with change reuse across 5 consecutive hops via bulletproof infrastructure.',
    nodes: [
      {
        id: '12dhqUGwzF6c6eW5F7DkyXyqBmW1',
        type: 'Wallet',
        label: '12dhq...BmW1 (Origin)',
        x: 14,
        y: 45,
        properties: {
          address: '12dhqUGwzF6c6eW5F7DkyXyqBmW1',
          is_licit_exchange: false,
          balance_btc: 14.52
        }
      },
      {
        id: 'tx_58234917',
        type: 'Transaction',
        label: 'TX:58234917',
        x: 28,
        y: 45,
        properties: {
          txid: 58234917,
          timestamp: '2026-09-03 04:12:00',
          fee_btc: 0.00035,
          script_type: 'P2PKH'
        }
      },
      {
        id: 'ip_38.148.127.142',
        type: 'IP',
        label: 'IP: 38.148.127.142',
        x: 28,
        y: 20,
        properties: {
          relay_ip: '38.148.127.142',
          country_code: 'IN',
          asn: 'AS55836',
          isp: 'Reliance Jio Infocomm',
          node_type: 'residential',
          relay_port: 8333,
          propagation_delta_ms: 188
        }
      },
      {
        id: '1EcgU6KKSdjtWmXzy5W3EX34ibCoH',
        type: 'Wallet',
        label: '1Ecg...bCoH (Peel #1)',
        x: 44,
        y: 28,
        properties: {
          address: '1EcgU6KKSdjtWmXzy5W3EX34ibCoH',
          is_licit_exchange: false,
          balance_btc: 0.0526
        }
      },
      {
        id: '1PZDhrao8CqYBnFzEk67TbPxX8MxbKjhmh',
        type: 'Wallet',
        label: '1PZD...jhmh (Change #1)',
        x: 44,
        y: 60,
        properties: {
          address: '1PZDhrao8CqYBnFzEk67TbPxX8MxbKjhmh',
          is_licit_exchange: false,
          balance_btc: 0.2106
        }
      },
      {
        id: 'tx_58234918',
        type: 'Transaction',
        label: 'TX:58234918',
        x: 58,
        y: 60,
        properties: {
          txid: 58234918,
          timestamp: '2026-09-03 04:13:30',
          fee_btc: 0.00034,
          script_type: 'P2PKH'
        }
      },
      {
        id: 'ip_185.220.101.5',
        type: 'IP',
        label: 'IP: 185.220.101.5 (Bulletproof)',
        x: 58,
        y: 85,
        properties: {
          relay_ip: '185.220.101.5',
          country_code: 'DE',
          asn: 'AS210644',
          isp: 'FlokiNET Bulletproof',
          node_type: 'bulletproof_host',
          relay_port: 8333,
          propagation_delta_ms: 64
        }
      },
      {
        id: '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
        type: 'Wallet',
        label: '1A1z...vfNa (Peel #2)',
        x: 74,
        y: 40,
        properties: {
          address: '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
          is_licit_exchange: false,
          balance_btc: 0.0526
        }
      },
      {
        id: '1BoatSLRHtKNngkdXEeobR76b53LETtpyT',
        type: 'Wallet',
        label: '1Boat...tpyT (Change #2)',
        x: 74,
        y: 72,
        properties: {
          address: '1BoatSLRHtKNngkdXEeobR76b53LETtpyT',
          is_licit_exchange: false,
          balance_btc: 0.1578
        }
      },
      {
        id: 'tx_58234922',
        type: 'Transaction',
        label: 'TX:58234922',
        x: 88,
        y: 72,
        properties: {
          txid: 58234922,
          timestamp: '2026-09-03 04:14:45',
          fee_btc: 0.00036,
          script_type: 'P2PKH'
        }
      }
    ],
    edges: [
      {
        id: 'e1',
        source: '12dhqUGwzF6c6eW5F7DkyXyqBmW1',
        target: 'tx_58234917',
        type: 'SENT',
        amount_btc: 0.2636
      },
      {
        id: 'e2',
        source: 'ip_38.148.127.142',
        target: 'tx_58234917',
        type: 'BROADCAST',
        relay_port: 8333,
        user_agent: '/Satoshi:22.0.0/'
      },
      {
        id: 'e3',
        source: 'tx_58234917',
        target: '1EcgU6KKSdjtWmXzy5W3EX34ibCoH',
        type: 'RECEIVED',
        amount_btc: 0.0526
      },
      {
        id: 'e4',
        source: 'tx_58234917',
        target: '1PZDhrao8CqYBnFzEk67TbPxX8MxbKjhmh',
        type: 'RECEIVED',
        amount_btc: 0.2106
      },
      {
        id: 'e5',
        source: '1PZDhrao8CqYBnFzEk67TbPxX8MxbKjhmh',
        target: 'tx_58234918',
        type: 'SENT',
        amount_btc: 0.2106
      },
      {
        id: 'e6',
        source: 'ip_185.220.101.5',
        target: 'tx_58234918',
        type: 'BROADCAST',
        relay_port: 8333,
        user_agent: '/Satoshi:23.0.0/'
      },
      {
        id: 'e7',
        source: 'tx_58234918',
        target: '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
        type: 'RECEIVED',
        amount_btc: 0.0526
      },
      {
        id: 'e8',
        source: 'tx_58234918',
        target: '1BoatSLRHtKNngkdXEeobR76b53LETtpyT',
        type: 'RECEIVED',
        amount_btc: 0.1578
      },
      {
        id: 'e9',
        source: '1BoatSLRHtKNngkdXEeobR76b53LETtpyT',
        target: 'tx_58234922',
        type: 'SENT',
        amount_btc: 0.1578
      }
    ],
    alerts: [
      {
        candidate_id: 'cand_peel_001_seq01',
        scenario_id: 'peel_001',
        predicted_pattern_type: 'peeling_chain',
        binary_confidence: 0.942,
        typology_confidence: 0.942,
        severity: 'CRITICAL',
        explanation: 'Sequential 1-in-2-out transactions peeling small outputs (avg 0.05 BTC) with change reuse across 5 consecutive hops via bulletproof infrastructure (AS210644).',
        primary_wallet: '12dhqUGwzF6c6eW5F7DkyXyqBmW1',
        member_txids: [58234917, 58234918, 58234922],
        member_wallets: [
          '12dhqUGwzF6c6eW5F7DkyXyqBmW1',
          '1EcgU6KKSdjtWmXzy5W3EX34ibCoH',
          '1PZDhrao8CqYBnFzEk67TbPxX8MxbKjhmh',
          '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'
        ],
        detected_at: '2026-09-03T04:15:00Z'
      }
    ],
    shap_attributions: [
      {
        feature_name: 'propagation_delta_ms',
        value: '188 ms',
        shap_value: 0.312,
        direction: 'RISK_INCREASING'
      },
      {
        feature_name: 'num_outputs (Peel signature)',
        value: 2,
        shap_value: 0.285,
        direction: 'RISK_INCREASING'
      },
      {
        feature_name: 'node_type_bulletproof_host',
        value: 'AS210644 (FlokiNET)',
        shap_value: 0.21,
        direction: 'RISK_INCREASING'
      },
      {
        feature_name: 'fee_ratio (Standard min fee)',
        value: '0.00133',
        shap_value: -0.045,
        direction: 'RISK_DECREASING'
      }
    ],
    telemetry: {
      origin_ips: ['38.148.127.142', '185.220.101.5'],
      origin_asns: ['AS55836', 'AS210644'],
      countries: ['IN', 'DE'],
      infrastructure_distribution: {
        residential: 1,
        bulletproof_host: 2
      }
    }
  },

  layer_014: {
    id: 'layer_014',
    name: 'Rapid Layering Fan-Out (8 Intermediaries)',
    pattern_type: 'layering',
    confidence: 0.887,
    severity: 'HIGH',
    summary: 'Rapid fan-out from single UTXO into 8 intermediate addresses followed by 8-to-1 fan-in reconvergence within 12 minutes.',
    nodes: [
      {
        id: '1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2',
        type: 'Wallet',
        label: '1BvB...NVN2 (Root Source)',
        x: 15,
        y: 50,
        properties: {
          address: '1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2',
          is_licit_exchange: false,
          balance_btc: 8.5
        }
      },
      {
        id: 'tx_61092834',
        type: 'Transaction',
        label: 'TX:61092834 (Fan-Out)',
        x: 35,
        y: 50,
        properties: {
          txid: 61092834,
          timestamp: '2026-09-03 04:10:00',
          fee_btc: 0.0008,
          script_type: 'P2WPKH'
        }
      },
      {
        id: 'ip_103.246.224.12',
        type: 'IP',
        label: 'IP: 103.246.224.12 (VPN)',
        x: 35,
        y: 20,
        properties: {
          relay_ip: '103.246.224.12',
          country_code: 'SG',
          asn: 'AS13335',
          isp: 'Mullvad VPN Relay',
          node_type: 'vpn',
          relay_port: 8333,
          propagation_delta_ms: 310
        }
      },
      {
        id: '13AM4VW2dhxYgXeQepoHkHSQuy6NgaEb94',
        type: 'Wallet',
        label: '13AM...Eb94 (Hub A)',
        x: 55,
        y: 30,
        properties: {
          address: '13AM4VW2dhxYgXeQepoHkHSQuy6NgaEb94',
          is_licit_exchange: false,
          balance_btc: 2.1
        }
      },
      {
        id: '1dice8EMZmqKvrGE4Qc9bUFf9PX3xaYDp',
        type: 'Wallet',
        label: '1dice...aYDp (Hub B)',
        x: 55,
        y: 70,
        properties: {
          address: '1dice8EMZmqKvrGE4Qc9bUFf9PX3xaYDp',
          is_licit_exchange: false,
          balance_btc: 2.1
        }
      },
      {
        id: 'tx_61092840',
        type: 'Transaction',
        label: 'TX:61092840 (Reconverge)',
        x: 75,
        y: 50,
        properties: {
          txid: 61092840,
          timestamp: '2026-09-03 04:22:00',
          fee_btc: 0.00095,
          script_type: 'P2WPKH'
        }
      },
      {
        id: '1CounterpartyXXXXXXXXXXXXXXXUWLpVr',
        type: 'Wallet',
        label: '1Coun...LpVr (Cashout)',
        x: 90,
        y: 50,
        properties: {
          address: '1CounterpartyXXXXXXXXXXXXXXXUWLpVr',
          is_licit_exchange: true,
          balance_btc: 4.19
        }
      }
    ],
    edges: [
      {
        id: 'le1',
        source: '1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2',
        target: 'tx_61092834',
        type: 'SENT',
        amount_btc: 8.5
      },
      {
        id: 'le2',
        source: 'ip_103.246.224.12',
        target: 'tx_61092834',
        type: 'BROADCAST',
        relay_port: 8333,
        user_agent: '/Satoshi:24.0.1/'
      },
      {
        id: 'le3',
        source: 'tx_61092834',
        target: '13AM4VW2dhxYgXeQepoHkHSQuy6NgaEb94',
        type: 'RECEIVED',
        amount_btc: 2.1
      },
      {
        id: 'le4',
        source: 'tx_61092834',
        target: '1dice8EMZmqKvrGE4Qc9bUFf9PX3xaYDp',
        type: 'RECEIVED',
        amount_btc: 2.1
      },
      {
        id: 'le5',
        source: '13AM4VW2dhxYgXeQepoHkHSQuy6NgaEb94',
        target: 'tx_61092840',
        type: 'SENT',
        amount_btc: 2.1
      },
      {
        id: 'le6',
        source: '1dice8EMZmqKvrGE4Qc9bUFf9PX3xaYDp',
        target: 'tx_61092840',
        type: 'SENT',
        amount_btc: 2.1
      },
      {
        id: 'le7',
        source: 'tx_61092840',
        target: '1CounterpartyXXXXXXXXXXXXXXXUWLpVr',
        type: 'RECEIVED',
        amount_btc: 4.19
      }
    ],
    alerts: [
      {
        candidate_id: 'cand_layer_014_seq02',
        scenario_id: 'layer_014',
        predicted_pattern_type: 'layering',
        binary_confidence: 0.887,
        typology_confidence: 0.887,
        severity: 'HIGH',
        explanation: 'Rapid fan-out from single UTXO into 8 intermediate addresses followed by 8-to-1 fan-in reconvergence within 12 minutes.',
        primary_wallet: '1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2',
        member_txids: [61092834, 61092840],
        member_wallets: [
          '1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2',
          '13AM4VW2dhxYgXeQepoHkHSQuy6NgaEb94',
          '1CounterpartyXXXXXXXXXXXXXXXUWLpVr'
        ],
        detected_at: '2026-09-03T04:12:10Z'
      }
    ],
    shap_attributions: [
      {
        feature_name: 'reconvergence_velocity_sec',
        value: '720s (12m)',
        shap_value: 0.384,
        direction: 'RISK_INCREASING'
      },
      {
        feature_name: 'fan_out_degree',
        value: 8,
        shap_value: 0.291,
        direction: 'RISK_INCREASING'
      },
      {
        feature_name: 'node_type_vpn_relay',
        value: 'Mullvad SG (AS13335)',
        shap_value: 0.178,
        direction: 'RISK_INCREASING'
      },
      {
        feature_name: 'output_entropy_score',
        value: '0.84',
        shap_value: 0.125,
        direction: 'RISK_INCREASING'
      }
    ],
    telemetry: {
      origin_ips: ['103.246.224.12', '45.142.212.8'],
      origin_asns: ['AS13335', 'AS209854'],
      countries: ['SG', 'NL'],
      infrastructure_distribution: {
        vpn: 1,
        tor_exit: 1
      }
    }
  },

  mix_003: {
    id: 'mix_003',
    name: 'Wasabi / CoinJoin Mixing Swarm',
    pattern_type: 'mixing',
    confidence: 0.764,
    severity: 'MEDIUM',
    summary: 'High-entropy CoinJoin mixing pool aggregating 16 independent inputs with uniform 0.1 BTC denominations.',
    nodes: [
      {
        id: '1Lbcfr7sAHTD9CgdQo3HTMTkV8LK4ZnX71',
        type: 'Wallet',
        label: '1Lbc...nX71 (Tainted)',
        x: 18,
        y: 35,
        properties: {
          address: '1Lbcfr7sAHTD9CgdQo3HTMTkV8LK4ZnX71',
          is_licit_exchange: false,
          balance_btc: 1.6
        }
      },
      {
        id: '1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF',
        type: 'Wallet',
        label: '1Feex...sb6uF',
        x: 18,
        y: 65,
        properties: {
          address: '1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF',
          is_licit_exchange: false,
          balance_btc: 3.2
        }
      },
      {
        id: 'tx_72849103',
        type: 'Transaction',
        label: 'TX:72849103 (CoinJoin Pool)',
        x: 50,
        y: 50,
        properties: {
          txid: 72849103,
          timestamp: '2026-09-03 04:05:12',
          fee_btc: 0.0018,
          script_type: 'P2TR (Taproot)'
        }
      },
      {
        id: 'ip_192.42.116.16',
        type: 'IP',
        label: 'IP: Tor Exit Node (NL)',
        x: 50,
        y: 18,
        properties: {
          relay_ip: '192.42.116.16',
          country_code: 'NL',
          asn: 'AS1103',
          isp: 'SURFnet Tor Exit',
          node_type: 'tor_exit',
          relay_port: 9001,
          propagation_delta_ms: 540
        }
      },
      {
        id: '17A16QmavnUfCW11DAApiJxp7ARnxN5pPE',
        type: 'Wallet',
        label: '17A1...5pPE (Anonymized)',
        x: 82,
        y: 35,
        properties: {
          address: '17A16QmavnUfCW11DAApiJxp7ARnxN5pPE',
          is_licit_exchange: false,
          balance_btc: 0.1
        }
      },
      {
        id: '12c6DSiU4Rq3P4ZxziKxzrL5LmMBrzjrJX',
        type: 'Wallet',
        label: '12c6...jrJX (Anonymized)',
        x: 82,
        y: 65,
        properties: {
          address: '12c6DSiU4Rq3P4ZxziKxzrL5LmMBrzjrJX',
          is_licit_exchange: false,
          balance_btc: 0.1
        }
      }
    ],
    edges: [
      {
        id: 'me1',
        source: '1Lbcfr7sAHTD9CgdQo3HTMTkV8LK4ZnX71',
        target: 'tx_72849103',
        type: 'SENT',
        amount_btc: 1.6
      },
      {
        id: 'me2',
        source: '1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF',
        target: 'tx_72849103',
        type: 'SENT',
        amount_btc: 3.2
      },
      {
        id: 'me3',
        source: 'ip_192.42.116.16',
        target: 'tx_72849103',
        type: 'BROADCAST',
        relay_port: 9001,
        user_agent: '/WasabiCoordinator:2.0/'
      },
      {
        id: 'me4',
        source: 'tx_72849103',
        target: '17A16QmavnUfCW11DAApiJxp7ARnxN5pPE',
        type: 'RECEIVED',
        amount_btc: 0.1
      },
      {
        id: 'me5',
        source: 'tx_72849103',
        target: '12c6DSiU4Rq3P4ZxziKxzrL5LmMBrzjrJX',
        type: 'RECEIVED',
        amount_btc: 0.1
      }
    ],
    alerts: [
      {
        candidate_id: 'cand_mix_003_seq09',
        scenario_id: 'mix_003',
        predicted_pattern_type: 'mixing',
        binary_confidence: 0.764,
        typology_confidence: 0.764,
        severity: 'MEDIUM',
        explanation: 'CoinJoin mixing pool execution with uniform 0.1 BTC denominations routed via Tor exit infrastructure to obfuscate UTXO lineage.',
        primary_wallet: '1Lbcfr7sAHTD9CgdQo3HTMTkV8LK4ZnX71',
        member_txids: [72849103],
        member_wallets: [
          '1Lbcfr7sAHTD9CgdQo3HTMTkV8LK4ZnX71',
          '17A16QmavnUfCW11DAApiJxp7ARnxN5pPE'
        ],
        detected_at: '2026-09-03T04:06:00Z'
      }
    ],
    shap_attributions: [
      {
        feature_name: 'shannon_entropy_inputs',
        value: '3.92',
        shap_value: 0.418,
        direction: 'RISK_INCREASING'
      },
      {
        feature_name: 'node_type_tor_exit',
        value: 'SURFnet (AS1103)',
        shap_value: 0.315,
        direction: 'RISK_INCREASING'
      },
      {
        feature_name: 'denomination_uniformity',
        value: '1.00 (0.1 BTC exact)',
        shap_value: 0.224,
        direction: 'RISK_INCREASING'
      },
      {
        feature_name: 'round_amount_penalty',
        value: '0.00',
        shap_value: -0.015,
        direction: 'RISK_DECREASING'
      }
    ],
    telemetry: {
      origin_ips: ['192.42.116.16'],
      origin_asns: ['AS1103'],
      countries: ['NL'],
      infrastructure_distribution: {
        tor_exit: 1
      }
    }
  }
};
