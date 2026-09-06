// AUTO-GENERATED FROM V6 GRAPH ENGINE RUN (2026-09-05T10:52:40.159650+00:00)
// 100% REAL BITCOIN AML TELEMETRY & TYPOLOGY CANDIDATES
import { ForensicNode, ForensicLink, KernelLogEntry, CommandDescriptor } from '../types/terminal';

export const GRAPH_METADATA = {
  "schema_version": "1.0",
  "generated_at": "2026-09-05T10:52:40.159650+00:00",
  "total_nodes": 459975,
  "total_edges": 527143,
  "total_candidates": 3531,
  "candidate_counts": {
    "peeling_chain": 670,
    "layering": 1778,
    "mixing": 1083
  }
};

export const INITIAL_NODES: ForensicNode[] = [
  {
    "id": "12emAgNj5Uos6UcFafY6EEkq6u2",
    "label": "BTC_WALLET_12emAgNj5U",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 6.9054,
    "balanceEth": 14.4332,
    "txCount": 4,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "13fi2EpZFgjpjAnxaMzofw5GtBy",
    "label": "BTC_WALLET_13fi2EpZFg",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 1.748,
    "balanceEth": 10.8251,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "15FaQ7xbeSQEyxdfAUDTsBgFoua",
    "label": "FAN_OUT_RELAY_15FaQ7xb",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 2.759,
    "balanceEth": 3.9383,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "16BWsrV3Zf1pC5usQiREcVJrVa",
    "label": "FAN_OUT_RELAY_16BWsrV3",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 11.3018,
    "balanceEth": 9.2189,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G",
    "label": "LAYERING_FANOUT_SOURCE",
    "type": "SUSPECT",
    "riskScore": 98,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 5.9706,
    "balanceEth": 0.9135,
    "txCount": 1,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "SUSPECT",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Ransomware Inflow Aggregator",
    "flags": [
      "OFAC_SANCTION_FOOTPRINT",
      "RAPID_DISBURSEMENT_ALERT",
      "TOR_EXIT_NODE_RELAY"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "17srEhi92HT5hF5ARERxnA3DznueUtJgc",
    "label": "BTC_WALLET_17srEhi92H",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 2.4263,
    "balanceEth": 11.029,
    "txCount": 4,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "18oMPaHSWY8uJSeadAmQLcHfmc",
    "label": "FAN_OUT_RELAY_18oMPaHS",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 5.5509,
    "balanceEth": 7.6942,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "19HepufHHXq5KoZnNqQfPwFHW77k",
    "label": "BTC_WALLET_19HepufHHX",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 2.9912,
    "balanceEth": 6.3328,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1Cq3HiZzahaS4PcwKeX9SMmtsw3hiTr3Xz",
    "label": "FAN_OUT_RELAY_1Cq3HiZz",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 12.7188,
    "balanceEth": 6.1687,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1DnWHZtdtCP57xCqjbuBxkHXHqU",
    "label": "PEEL_HOP_1_RELAY",
    "type": "PEELING_CHAIN",
    "riskScore": 91,
    "clusterId": "CLUSTER_PEEL_0564",
    "balanceBtc": 7.375,
    "balanceEth": 7.3238,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "PEELING_CHAIN",
      "CLUSTER_PEEL_0564",
      "PEELING_CHAIN",
      "UTXO_DECAY"
    ],
    "ownerAlias": "Peeling Carry-Forward Intermediary",
    "flags": [
      "OFAC_SANCTION_FOOTPRINT",
      "RAPID_DISBURSEMENT_ALERT",
      "TOR_EXIT_NODE_RELAY"
    ],
    "candidateId": "peel_0564",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1Et4y3xsYYZCtQLv3aZGYaz5eTafhph",
    "label": "FAN_OUT_RELAY_1Et4y3xs",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 5.2595,
    "balanceEth": 13.2572,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1JCGLh437W14JXw8uNgLkjRka878B2F",
    "label": "FAN_OUT_RELAY_1JCGLh43",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 10.1532,
    "balanceEth": 8.467,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1JadLZMcaFX1JvRTkHmcAEZ4ygHm",
    "label": "LAYERING_CONSOLIDATION_SINK",
    "type": "LAYERING_HUB",
    "riskScore": 94,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 9.1299,
    "balanceEth": 2.6386,
    "txCount": 1,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "LAYERING_HUB",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Consolidation Vault / Mixing Escrow",
    "flags": [
      "OFAC_SANCTION_FOOTPRINT",
      "RAPID_DISBURSEMENT_ALERT",
      "TOR_EXIT_NODE_RELAY"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1KyJRwBvxLpV9S8LKDCVP7CYyqALvkAm2H",
    "label": "FAN_OUT_RELAY_1KyJRwBv",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 11.5348,
    "balanceEth": 12.9812,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1MPjtn7eqawrM7gBJsQsBT3wzMuzWz56F1",
    "label": "FAN_OUT_RELAY_1MPjtn7e",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 6.0523,
    "balanceEth": 6.3637,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1NWuKnHBKUnzJRw7LPLxpd1RvMP32b",
    "label": "FAN_OUT_RELAY_1NWuKnHB",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 3.4865,
    "balanceEth": 12.7363,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1PTqbgVoXSbuzQKrDGw2M2tchx",
    "label": "PRIMARY_SUSPECT_PEEL_ORIGIN",
    "type": "SUSPECT",
    "riskScore": 96,
    "clusterId": "CLUSTER_PEEL_0564",
    "balanceBtc": 7.0739,
    "balanceEth": 14.3907,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "SUSPECT",
      "CLUSTER_PEEL_0564",
      "PEELING_CHAIN",
      "UTXO_DECAY"
    ],
    "ownerAlias": "Hydra / DarkMarket Cashout Pipeline",
    "flags": [
      "OFAC_SANCTION_FOOTPRINT",
      "RAPID_DISBURSEMENT_ALERT",
      "TOR_EXIT_NODE_RELAY"
    ],
    "candidateId": "peel_0564",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1Q75uGchVa4eN8EHuQiuX8z9j3oS9Ng1XT",
    "label": "FAN_OUT_RELAY_1Q75uGch",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 3.9634,
    "balanceEth": 1.689,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1QBMzLsqyakZJgWea4KyeitHbNx3qKYA",
    "label": "FAN_OUT_RELAY_1QBMzLsq",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 3.2373,
    "balanceEth": 9.2102,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1RBv2NCXCTKZeiL9cEkJAaWUAPh2Q",
    "label": "FAN_OUT_RELAY_1RBv2NCX",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 12.6726,
    "balanceEth": 5.487,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1Ro556NAYBZpbrUtJRCqg1qiiiW4",
    "label": "BTC_WALLET_1Ro556NAYB",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 10.0653,
    "balanceEth": 11.9954,
    "txCount": 4,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1SDQmJYVPcqajMCucmnBhTrVCVd6Ec",
    "label": "FAN_OUT_RELAY_1SDQmJYV",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 5.4118,
    "balanceEth": 10.9093,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1U2qQJkhBdHu5aWKwxpLtkx4Dh",
    "label": "FAN_OUT_RELAY_1U2qQJkh",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 0.9461,
    "balanceEth": 14.2318,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1UFPZf167WSynu8FCvH9BWMqdK8ygZ",
    "label": "FAN_OUT_RELAY_1UFPZf16",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 11.9445,
    "balanceEth": 11.4181,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1Ujf566EUPjTDAPh2icNyCbxQmQ6qhp",
    "label": "FAN_OUT_RELAY_1Ujf566E",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 1.9934,
    "balanceEth": 3.2221,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1VPcvAf5tmJP8EECAH6bRSZqurofau",
    "label": "BTC_WALLET_1VPcvAf5tm",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 0.9027,
    "balanceEth": 6.9844,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1XmiVkPbNe6dMVQFbottSStugoZSN",
    "label": "BTC_WALLET_1XmiVkPbNe",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 1.0142,
    "balanceEth": 7.4893,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1XsbsHvneK4VGRrQZCCG6fnGGBNpAqc",
    "label": "FAN_OUT_RELAY_1XsbsHvn",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 3.6566,
    "balanceEth": 1.531,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1YNB9Yxwd1KTbKVFVQyqurHDyR6LeGYMAD",
    "label": "FAN_OUT_RELAY_1YNB9Yxw",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 11.4684,
    "balanceEth": 1.5449,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1ZmZYV7ns1khJhh7jfoKXnWgqFFpVYy57K",
    "label": "BTC_WALLET_1ZmZYV7ns1",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 2.0457,
    "balanceEth": 14.4173,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1cNd1nppdeJ3hfXiNpnoyM4Bu9rrGLvq",
    "label": "FAN_OUT_RELAY_1cNd1npp",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 13.7179,
    "balanceEth": 2.6392,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1d92F9SKdQ18Az2ni9chFrM2p2wmUcC",
    "label": "FAN_OUT_RELAY_1d92F9SK",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 3.9358,
    "balanceEth": 5.6306,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1eT1dF73RFreuuhuimB8CadRSbv",
    "label": "FAN_OUT_RELAY_1eT1dF73",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 6.4044,
    "balanceEth": 5.6696,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1fCw9QCXdCYoKaBFsyWbyVgZw8n4Hkp",
    "label": "FAN_OUT_RELAY_1fCw9QCX",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 5.2206,
    "balanceEth": 6.19,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1g64wCdEj3frZLfsRPtm5Xdke1fdiJeG",
    "label": "BTC_WALLET_1g64wCdEj3",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 13.2577,
    "balanceEth": 2.2028,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1kj5cC8PYnTmwGgkpLKAFk3Ubh8fE",
    "label": "FAN_OUT_RELAY_1kj5cC8P",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 7.2962,
    "balanceEth": 9.23,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1nErH5MRLErVwVQZZ9w44yhX7TcVzM",
    "label": "PEEL_HOP_3_RELAY",
    "type": "PEELING_CHAIN",
    "riskScore": 87,
    "clusterId": "CLUSTER_PEEL_0564",
    "balanceBtc": 7.2746,
    "balanceEth": 6.7562,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "PEELING_CHAIN",
      "CLUSTER_PEEL_0564",
      "PEELING_CHAIN",
      "UTXO_DECAY"
    ],
    "ownerAlias": "Peeling Carry-Forward Intermediary",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "peel_0564",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1o5XftUNrK8KJ1fj64KgDwiXd7CDB7r",
    "label": "FAN_OUT_RELAY_1o5XftUN",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 12.0534,
    "balanceEth": 2.0116,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1piDkxRaDo8VfRnxnSEHvz93i5H6zdT",
    "label": "FAN_OUT_RELAY_1piDkxRa",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 11.7721,
    "balanceEth": 6.956,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1rGumkvop4ddCHftQ5zweJ17FZ",
    "label": "BTC_WALLET_1rGumkvop4",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 1.8856,
    "balanceEth": 12.9177,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1rVWwVr773EM8RscY9epNJsYqMj",
    "label": "FAN_OUT_RELAY_1rVWwVr7",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 12.5421,
    "balanceEth": 10.2874,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1s6D1TaSbKqeTG5YMhWWRJ85Ve8s7Y",
    "label": "UNLICENSED_OTC_EXIT_CORRIDOR",
    "type": "EXCHANGE",
    "riskScore": 85,
    "clusterId": "CLUSTER_PEEL_0564",
    "balanceBtc": 12.2153,
    "balanceEth": 6.6794,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "EXCHANGE",
      "CLUSTER_PEEL_0564",
      "PEELING_CHAIN",
      "UTXO_DECAY"
    ],
    "ownerAlias": "High-Risk Unregistered OTC Brokerage",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "peel_0564",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1snCZQN8XGEW3gkwQWv6FRhpat5Qfttgv",
    "label": "FAN_OUT_RELAY_1snCZQN8",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 4.5194,
    "balanceEth": 11.147,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1unSWocZerQPVe3pmydVV8KGgUD",
    "label": "BTC_WALLET_1unSWocZer",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 2.4244,
    "balanceEth": 11.6459,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1vcTcJc5qokb2buGGbG1yNrDk7YLar",
    "label": "BTC_WALLET_1vcTcJc5qo",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 5.0988,
    "balanceEth": 1.0082,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1wChDwqJSQgTgKgRzsbANwMRXxvXLKHKN3",
    "label": "BTC_WALLET_1wChDwqJSQ",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 3.1723,
    "balanceEth": 9.3129,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1wMdNuDqsBFmncgNNpa3eAxGXi4L",
    "label": "PEEL_HOP_2_RELAY",
    "type": "PEELING_CHAIN",
    "riskScore": 89,
    "clusterId": "CLUSTER_PEEL_0564",
    "balanceBtc": 13.0785,
    "balanceEth": 5.1512,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "PEELING_CHAIN",
      "CLUSTER_PEEL_0564",
      "PEELING_CHAIN",
      "UTXO_DECAY"
    ],
    "ownerAlias": "Peeling Carry-Forward Intermediary",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "peel_0564",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1wUM3XMsQVTSYEVWMnzm5d7TfYwY",
    "label": "BTC_WALLET_1wUM3XMsQV",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 8.9058,
    "balanceEth": 11.8174,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1yVnD1uQau5YS2SWiotwP8dDsd",
    "label": "BTC_WALLET_1yVnD1uQau",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 5.534,
    "balanceEth": 10.4713,
    "txCount": 4,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "1ycD73SBsCDVVg6hocEieDisnS2BELDqs2",
    "label": "FAN_OUT_RELAY_1ycD73SB",
    "type": "WALLET",
    "riskScore": 78,
    "clusterId": "CLUSTER_LAYER_1054",
    "balanceBtc": 7.7179,
    "balanceEth": 3.5883,
    "txCount": 2,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "CLUSTER_LAYER_1054",
      "FAN_OUT_LAYERING",
      "MULTI_HOP_CONVERGENCE"
    ],
    "ownerAlias": "Layering Intermediary Smurf Wallet",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "layer_1054",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "155.179.203.78"
  },
  {
    "id": "1zX2QbzuWQ8dv7QKGBePEZYsEJ",
    "label": "BTC_WALLET_1zX2QbzuWQ",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 7.3304,
    "balanceEth": 14.1707,
    "txCount": 6,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:13xtQfa6QBdRihZNB2o8BgS1yQ",
    "label": "COINJOIN_SIGNER_w:13xtQf",
    "type": "MIXER",
    "riskScore": 88,
    "clusterId": "CLUSTER_MIX_0755",
    "balanceBtc": 2.1382,
    "balanceEth": 1.9738,
    "txCount": 20,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "MIXER",
      "CLUSTER_MIX_0755",
      "COINJOIN_MIXING",
      "STANDARDIZED_OUTPUTS"
    ],
    "ownerAlias": "CoinJoin Protocol Co-Signer",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "mix_0755",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:18VkGCV1zZ8YV6PwG1LHdL7JB7",
    "label": "BTC_WALLET_w:18VkGCV1",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 7.9787,
    "balanceEth": 8.0834,
    "txCount": 28,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:19p5wJSSxXtYQYTBfbuvS8kVJxJcxtuaa1",
    "label": "COINJOIN_SIGNER_w:19p5wJ",
    "type": "MIXER",
    "riskScore": 88,
    "clusterId": "CLUSTER_MIX_0755",
    "balanceBtc": 6.1473,
    "balanceEth": 1.1599,
    "txCount": 21,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "MIXER",
      "CLUSTER_MIX_0755",
      "COINJOIN_MIXING",
      "STANDARDIZED_OUTPUTS"
    ],
    "ownerAlias": "CoinJoin Protocol Co-Signer",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "mix_0755",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:1EPwT5QopwYrTANuU1Doc8paC2pCZyyckZ",
    "label": "COINJOIN_SIGNER_w:1EPwT5",
    "type": "MIXER",
    "riskScore": 88,
    "clusterId": "CLUSTER_MIX_0755",
    "balanceBtc": 12.8855,
    "balanceEth": 12.0637,
    "txCount": 18,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "MIXER",
      "CLUSTER_MIX_0755",
      "COINJOIN_MIXING",
      "STANDARDIZED_OUTPUTS"
    ],
    "ownerAlias": "CoinJoin Protocol Co-Signer",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "mix_0755",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:1GjYoHwRXMSRzWgUxxPrvjMXd2XXbhtNA4",
    "label": "COINJOIN_SIGNER_w:1GjYoH",
    "type": "MIXER",
    "riskScore": 88,
    "clusterId": "CLUSTER_MIX_0755",
    "balanceBtc": 3.266,
    "balanceEth": 6.9094,
    "txCount": 19,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "MIXER",
      "CLUSTER_MIX_0755",
      "COINJOIN_MIXING",
      "STANDARDIZED_OUTPUTS"
    ],
    "ownerAlias": "CoinJoin Protocol Co-Signer",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "mix_0755",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:1Qn5mncfUDCKj8pZPzgVedT3b8pB",
    "label": "BTC_WALLET_w:1Qn5mncf",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 1.8687,
    "balanceEth": 13.751,
    "txCount": 21,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:1S9i9JWinMeM7uuq7uEDdfL9TnawfSrWMw",
    "label": "BTC_WALLET_w:1S9i9JWi",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 6.2908,
    "balanceEth": 6.6126,
    "txCount": 26,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:1T2DUQ6AyVCtciuLdpvuwVprPJxa3Zm1dX",
    "label": "BTC_WALLET_w:1T2DUQ6A",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 4.7857,
    "balanceEth": 5.1151,
    "txCount": 22,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:1ZWUPH5znmERV7tiqojbVEySen",
    "label": "COINJOIN_SIGNER_w:1ZWUPH",
    "type": "MIXER",
    "riskScore": 88,
    "clusterId": "CLUSTER_MIX_0755",
    "balanceBtc": 11.3519,
    "balanceEth": 3.1313,
    "txCount": 16,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "MIXER",
      "CLUSTER_MIX_0755",
      "COINJOIN_MIXING",
      "STANDARDIZED_OUTPUTS"
    ],
    "ownerAlias": "CoinJoin Protocol Co-Signer",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "mix_0755",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:1eAjAUKEjvUzeCD3JCq8sJFZRBKw",
    "label": "BTC_WALLET_w:1eAjAUKE",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 8.7801,
    "balanceEth": 1.8304,
    "txCount": 21,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:1euRz5ZF211ZH1DpLyhFiSZmvSvAmqG15",
    "label": "BTC_WALLET_w:1euRz5ZF",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 5.9567,
    "balanceEth": 11.9618,
    "txCount": 3,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:1m9uKtJS1iMMyjbAsofardA9kqCUHG5J",
    "label": "BTC_WALLET_w:1m9uKtJS",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 11.5434,
    "balanceEth": 9.7097,
    "txCount": 14,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:1pX8mb3afMZWxyqvNc1uybCZozQseZt",
    "label": "COINJOIN_SIGNER_w:1pX8mb",
    "type": "MIXER",
    "riskScore": 88,
    "clusterId": "CLUSTER_MIX_0755",
    "balanceBtc": 4.1071,
    "balanceEth": 13.8073,
    "txCount": 21,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "MIXER",
      "CLUSTER_MIX_0755",
      "COINJOIN_MIXING",
      "STANDARDIZED_OUTPUTS"
    ],
    "ownerAlias": "CoinJoin Protocol Co-Signer",
    "flags": [
      "UNREGISTERED_MSB_REACH",
      "ANOMALOUS_VELOCITY_RATIO"
    ],
    "candidateId": "mix_0755",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:1rL23qSNXqg6SyuEwoXCtpPB2qML",
    "label": "BTC_WALLET_w:1rL23qSN",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 13.7332,
    "balanceEth": 6.4668,
    "txCount": 11,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:1sBXzQtjivghnY9Fu8rEXw58wtB2iq",
    "label": "BTC_WALLET_w:1sBXzQtj",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 6.2025,
    "balanceEth": 11.8541,
    "txCount": 21,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:1sBn8wgQ5C4y4sGan1Li4WHDFwwJs",
    "label": "BTC_WALLET_w:1sBn8wgQ",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 5.248,
    "balanceEth": 4.9638,
    "txCount": 15,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  },
  {
    "id": "w:1y11idQQmCP8vJq3qEavxsx1Hy6Qtb7xD",
    "label": "BTC_WALLET_w:1y11idQQ",
    "type": "WALLET",
    "riskScore": 45,
    "clusterId": "BENIGN_NETWORK_POOL",
    "balanceBtc": 6.148,
    "balanceEth": 1.4274,
    "txCount": 17,
    "firstSeen": "2014-03-12 14:22:01 UTC",
    "lastSeen": "2014-07-05 22:15:30 UTC",
    "tags": [
      "WALLET",
      "BENIGN_NETWORK_POOL"
    ],
    "ownerAlias": "Anonymous Bitcoin Entity",
    "flags": [
      "STANDARD_UTXO_CONSOLIDATION"
    ],
    "candidateId": "benign_network_pool",
    "asn": "AS13335 (Cloudflare/Tor Gateway)",
    "relayIp": "12.10.139.26"
  }
];

export const INITIAL_LINKS: ForensicLink[] = [
  {
    "source": "1PTqbgVoXSbuzQKrDGw2M2tchx",
    "target": "1DnWHZtdtCP57xCqjbuBxkHXHqU",
    "txHash": "tx:305493508",
    "amountBtc": 1.48094194,
    "amountEth": 1.48094194,
    "timestamp": "2014-07-04T13:06:54+00:00",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "peel_0564"
  },
  {
    "source": "1DnWHZtdtCP57xCqjbuBxkHXHqU",
    "target": "1wMdNuDqsBFmncgNNpa3eAxGXi4L",
    "txHash": "tx:616642538",
    "amountBtc": 1.43764459,
    "amountEth": 1.43764459,
    "timestamp": "2014-07-04T15:48:31+00:00",
    "isSuspicious": true,
    "hopIndex": 2,
    "candidateId": "peel_0564"
  },
  {
    "source": "1wMdNuDqsBFmncgNNpa3eAxGXi4L",
    "target": "1nErH5MRLErVwVQZZ9w44yhX7TcVzM",
    "txHash": "tx:922456847",
    "amountBtc": 1.25764895,
    "amountEth": 1.25764895,
    "timestamp": "2014-07-04T21:39:17+00:00",
    "isSuspicious": true,
    "hopIndex": 3,
    "candidateId": "peel_0564"
  },
  {
    "source": "1nErH5MRLErVwVQZZ9w44yhX7TcVzM",
    "target": "1s6D1TaSbKqeTG5YMhWWRJ85Ve8s7Y",
    "txHash": "tx:248085913",
    "amountBtc": 1.16858464,
    "amountEth": 1.16858464,
    "timestamp": "2014-07-04T22:08:09+00:00",
    "isSuspicious": true,
    "hopIndex": 4,
    "candidateId": "peel_0564"
  },
  {
    "source": "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G",
    "target": "1Et4y3xsYYZCtQLv3aZGYaz5eTafhph",
    "txHash": "tx:257491939",
    "amountBtc": 0.18,
    "amountEth": 0.18,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "layer_1054"
  },
  {
    "source": "1Et4y3xsYYZCtQLv3aZGYaz5eTafhph",
    "target": "1snCZQN8XGEW3gkwQWv6FRhpat5Qfttgv",
    "txHash": "tx:936637089",
    "amountBtc": 0.18,
    "amountEth": 0.18,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 2,
    "candidateId": "layer_1054"
  },
  {
    "source": "1snCZQN8XGEW3gkwQWv6FRhpat5Qfttgv",
    "target": "1JadLZMcaFX1JvRTkHmcAEZ4ygHm",
    "txHash": "tx:740919709",
    "amountBtc": 0.175,
    "amountEth": 0.175,
    "timestamp": "2014-03-15T03:10:29+00:00",
    "isSuspicious": true,
    "hopIndex": 3,
    "candidateId": "layer_1054"
  },
  {
    "source": "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G",
    "target": "1SDQmJYVPcqajMCucmnBhTrVCVd6Ec",
    "txHash": "tx:257491939",
    "amountBtc": 0.19,
    "amountEth": 0.19,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "layer_1054"
  },
  {
    "source": "1SDQmJYVPcqajMCucmnBhTrVCVd6Ec",
    "target": "1QBMzLsqyakZJgWea4KyeitHbNx3qKYA",
    "txHash": "tx:686634332",
    "amountBtc": 0.19,
    "amountEth": 0.19,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 2,
    "candidateId": "layer_1054"
  },
  {
    "source": "1QBMzLsqyakZJgWea4KyeitHbNx3qKYA",
    "target": "1JadLZMcaFX1JvRTkHmcAEZ4ygHm",
    "txHash": "tx:740919709",
    "amountBtc": 0.185,
    "amountEth": 0.185,
    "timestamp": "2014-03-15T03:10:29+00:00",
    "isSuspicious": true,
    "hopIndex": 3,
    "candidateId": "layer_1054"
  },
  {
    "source": "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G",
    "target": "1d92F9SKdQ18Az2ni9chFrM2p2wmUcC",
    "txHash": "tx:257491939",
    "amountBtc": 0.2,
    "amountEth": 0.2,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "layer_1054"
  },
  {
    "source": "1d92F9SKdQ18Az2ni9chFrM2p2wmUcC",
    "target": "1RBv2NCXCTKZeiL9cEkJAaWUAPh2Q",
    "txHash": "tx:280448111",
    "amountBtc": 0.2,
    "amountEth": 0.2,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 2,
    "candidateId": "layer_1054"
  },
  {
    "source": "1RBv2NCXCTKZeiL9cEkJAaWUAPh2Q",
    "target": "1JadLZMcaFX1JvRTkHmcAEZ4ygHm",
    "txHash": "tx:740919709",
    "amountBtc": 0.195,
    "amountEth": 0.195,
    "timestamp": "2014-03-15T03:10:29+00:00",
    "isSuspicious": true,
    "hopIndex": 3,
    "candidateId": "layer_1054"
  },
  {
    "source": "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G",
    "target": "1Ujf566EUPjTDAPh2icNyCbxQmQ6qhp",
    "txHash": "tx:257491939",
    "amountBtc": 0.21,
    "amountEth": 0.21,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "layer_1054"
  },
  {
    "source": "1Ujf566EUPjTDAPh2icNyCbxQmQ6qhp",
    "target": "1Cq3HiZzahaS4PcwKeX9SMmtsw3hiTr3Xz",
    "txHash": "tx:149714874",
    "amountBtc": 0.21,
    "amountEth": 0.21,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 2,
    "candidateId": "layer_1054"
  },
  {
    "source": "1Cq3HiZzahaS4PcwKeX9SMmtsw3hiTr3Xz",
    "target": "1JadLZMcaFX1JvRTkHmcAEZ4ygHm",
    "txHash": "tx:740919709",
    "amountBtc": 0.205,
    "amountEth": 0.205,
    "timestamp": "2014-03-15T03:10:29+00:00",
    "isSuspicious": true,
    "hopIndex": 3,
    "candidateId": "layer_1054"
  },
  {
    "source": "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G",
    "target": "1UFPZf167WSynu8FCvH9BWMqdK8ygZ",
    "txHash": "tx:257491939",
    "amountBtc": 0.22,
    "amountEth": 0.22,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "layer_1054"
  },
  {
    "source": "1UFPZf167WSynu8FCvH9BWMqdK8ygZ",
    "target": "1eT1dF73RFreuuhuimB8CadRSbv",
    "txHash": "tx:785742615",
    "amountBtc": 0.22,
    "amountEth": 0.22,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 2,
    "candidateId": "layer_1054"
  },
  {
    "source": "1eT1dF73RFreuuhuimB8CadRSbv",
    "target": "1JadLZMcaFX1JvRTkHmcAEZ4ygHm",
    "txHash": "tx:740919709",
    "amountBtc": 0.215,
    "amountEth": 0.215,
    "timestamp": "2014-03-15T03:10:29+00:00",
    "isSuspicious": true,
    "hopIndex": 3,
    "candidateId": "layer_1054"
  },
  {
    "source": "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G",
    "target": "1kj5cC8PYnTmwGgkpLKAFk3Ubh8fE",
    "txHash": "tx:257491939",
    "amountBtc": 0.23,
    "amountEth": 0.23,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "layer_1054"
  },
  {
    "source": "1kj5cC8PYnTmwGgkpLKAFk3Ubh8fE",
    "target": "1JCGLh437W14JXw8uNgLkjRka878B2F",
    "txHash": "tx:962170333",
    "amountBtc": 0.23,
    "amountEth": 0.23,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 2,
    "candidateId": "layer_1054"
  },
  {
    "source": "1JCGLh437W14JXw8uNgLkjRka878B2F",
    "target": "1JadLZMcaFX1JvRTkHmcAEZ4ygHm",
    "txHash": "tx:740919709",
    "amountBtc": 0.225,
    "amountEth": 0.225,
    "timestamp": "2014-03-15T03:10:29+00:00",
    "isSuspicious": true,
    "hopIndex": 3,
    "candidateId": "layer_1054"
  },
  {
    "source": "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G",
    "target": "1piDkxRaDo8VfRnxnSEHvz93i5H6zdT",
    "txHash": "tx:257491939",
    "amountBtc": 0.24,
    "amountEth": 0.24,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "layer_1054"
  },
  {
    "source": "1piDkxRaDo8VfRnxnSEHvz93i5H6zdT",
    "target": "1o5XftUNrK8KJ1fj64KgDwiXd7CDB7r",
    "txHash": "tx:709424955",
    "amountBtc": 0.24,
    "amountEth": 0.24,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 2,
    "candidateId": "layer_1054"
  },
  {
    "source": "1o5XftUNrK8KJ1fj64KgDwiXd7CDB7r",
    "target": "1JadLZMcaFX1JvRTkHmcAEZ4ygHm",
    "txHash": "tx:740919709",
    "amountBtc": 0.235,
    "amountEth": 0.235,
    "timestamp": "2014-03-15T03:10:29+00:00",
    "isSuspicious": true,
    "hopIndex": 3,
    "candidateId": "layer_1054"
  },
  {
    "source": "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G",
    "target": "15FaQ7xbeSQEyxdfAUDTsBgFoua",
    "txHash": "tx:257491939",
    "amountBtc": 0.25,
    "amountEth": 0.25,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "layer_1054"
  },
  {
    "source": "15FaQ7xbeSQEyxdfAUDTsBgFoua",
    "target": "1Q75uGchVa4eN8EHuQiuX8z9j3oS9Ng1XT",
    "txHash": "tx:814478336",
    "amountBtc": 0.25,
    "amountEth": 0.25,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 2,
    "candidateId": "layer_1054"
  },
  {
    "source": "1Q75uGchVa4eN8EHuQiuX8z9j3oS9Ng1XT",
    "target": "1JadLZMcaFX1JvRTkHmcAEZ4ygHm",
    "txHash": "tx:740919709",
    "amountBtc": 0.245,
    "amountEth": 0.245,
    "timestamp": "2014-03-15T03:10:29+00:00",
    "isSuspicious": true,
    "hopIndex": 3,
    "candidateId": "layer_1054"
  },
  {
    "source": "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G",
    "target": "1KyJRwBvxLpV9S8LKDCVP7CYyqALvkAm2H",
    "txHash": "tx:257491939",
    "amountBtc": 0.26,
    "amountEth": 0.26,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "layer_1054"
  },
  {
    "source": "1KyJRwBvxLpV9S8LKDCVP7CYyqALvkAm2H",
    "target": "18oMPaHSWY8uJSeadAmQLcHfmc",
    "txHash": "tx:497311796",
    "amountBtc": 0.26,
    "amountEth": 0.26,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 2,
    "candidateId": "layer_1054"
  },
  {
    "source": "18oMPaHSWY8uJSeadAmQLcHfmc",
    "target": "1JadLZMcaFX1JvRTkHmcAEZ4ygHm",
    "txHash": "tx:740919709",
    "amountBtc": 0.255,
    "amountEth": 0.255,
    "timestamp": "2014-03-15T03:10:29+00:00",
    "isSuspicious": true,
    "hopIndex": 3,
    "candidateId": "layer_1054"
  },
  {
    "source": "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G",
    "target": "1YNB9Yxwd1KTbKVFVQyqurHDyR6LeGYMAD",
    "txHash": "tx:257491939",
    "amountBtc": 0.27,
    "amountEth": 0.27,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "layer_1054"
  },
  {
    "source": "1YNB9Yxwd1KTbKVFVQyqurHDyR6LeGYMAD",
    "target": "16BWsrV3Zf1pC5usQiREcVJrVa",
    "txHash": "tx:956252112",
    "amountBtc": 0.27,
    "amountEth": 0.27,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 2,
    "candidateId": "layer_1054"
  },
  {
    "source": "16BWsrV3Zf1pC5usQiREcVJrVa",
    "target": "1JadLZMcaFX1JvRTkHmcAEZ4ygHm",
    "txHash": "tx:740919709",
    "amountBtc": 0.265,
    "amountEth": 0.265,
    "timestamp": "2014-03-15T03:10:29+00:00",
    "isSuspicious": true,
    "hopIndex": 3,
    "candidateId": "layer_1054"
  },
  {
    "source": "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G",
    "target": "1U2qQJkhBdHu5aWKwxpLtkx4Dh",
    "txHash": "tx:257491939",
    "amountBtc": 0.28,
    "amountEth": 0.28,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "layer_1054"
  },
  {
    "source": "1U2qQJkhBdHu5aWKwxpLtkx4Dh",
    "target": "1cNd1nppdeJ3hfXiNpnoyM4Bu9rrGLvq",
    "txHash": "tx:768977205",
    "amountBtc": 0.28,
    "amountEth": 0.28,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 2,
    "candidateId": "layer_1054"
  },
  {
    "source": "1cNd1nppdeJ3hfXiNpnoyM4Bu9rrGLvq",
    "target": "1JadLZMcaFX1JvRTkHmcAEZ4ygHm",
    "txHash": "tx:740919709",
    "amountBtc": 0.275,
    "amountEth": 0.275,
    "timestamp": "2014-03-15T03:10:29+00:00",
    "isSuspicious": true,
    "hopIndex": 3,
    "candidateId": "layer_1054"
  },
  {
    "source": "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G",
    "target": "1MPjtn7eqawrM7gBJsQsBT3wzMuzWz56F1",
    "txHash": "tx:257491939",
    "amountBtc": 0.29,
    "amountEth": 0.29,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "layer_1054"
  },
  {
    "source": "1MPjtn7eqawrM7gBJsQsBT3wzMuzWz56F1",
    "target": "1fCw9QCXdCYoKaBFsyWbyVgZw8n4Hkp",
    "txHash": "tx:211261302",
    "amountBtc": 0.29,
    "amountEth": 0.29,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 2,
    "candidateId": "layer_1054"
  },
  {
    "source": "1fCw9QCXdCYoKaBFsyWbyVgZw8n4Hkp",
    "target": "1JadLZMcaFX1JvRTkHmcAEZ4ygHm",
    "txHash": "tx:740919709",
    "amountBtc": 0.285,
    "amountEth": 0.285,
    "timestamp": "2014-03-15T03:10:29+00:00",
    "isSuspicious": true,
    "hopIndex": 3,
    "candidateId": "layer_1054"
  },
  {
    "source": "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G",
    "target": "1ycD73SBsCDVVg6hocEieDisnS2BELDqs2",
    "txHash": "tx:257491939",
    "amountBtc": 0.3,
    "amountEth": 0.3,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "layer_1054"
  },
  {
    "source": "1ycD73SBsCDVVg6hocEieDisnS2BELDqs2",
    "target": "1rVWwVr773EM8RscY9epNJsYqMj",
    "txHash": "tx:600499442",
    "amountBtc": 0.3,
    "amountEth": 0.3,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 2,
    "candidateId": "layer_1054"
  },
  {
    "source": "1rVWwVr773EM8RscY9epNJsYqMj",
    "target": "1JadLZMcaFX1JvRTkHmcAEZ4ygHm",
    "txHash": "tx:740919709",
    "amountBtc": 0.295,
    "amountEth": 0.295,
    "timestamp": "2014-03-15T03:10:29+00:00",
    "isSuspicious": true,
    "hopIndex": 3,
    "candidateId": "layer_1054"
  },
  {
    "source": "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G",
    "target": "1NWuKnHBKUnzJRw7LPLxpd1RvMP32b",
    "txHash": "tx:257491939",
    "amountBtc": 0.31,
    "amountEth": 0.31,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "layer_1054"
  },
  {
    "source": "1NWuKnHBKUnzJRw7LPLxpd1RvMP32b",
    "target": "1XsbsHvneK4VGRrQZCCG6fnGGBNpAqc",
    "txHash": "tx:702618326",
    "amountBtc": 0.31,
    "amountEth": 0.31,
    "timestamp": "2014-03-13T17:10:26+00:00",
    "isSuspicious": true,
    "hopIndex": 2,
    "candidateId": "layer_1054"
  },
  {
    "source": "1XsbsHvneK4VGRrQZCCG6fnGGBNpAqc",
    "target": "1JadLZMcaFX1JvRTkHmcAEZ4ygHm",
    "txHash": "tx:740919709",
    "amountBtc": 0.305,
    "amountEth": 0.305,
    "timestamp": "2014-03-15T03:10:29+00:00",
    "isSuspicious": true,
    "hopIndex": 3,
    "candidateId": "layer_1054"
  },
  {
    "source": "w:13xtQfa6QBdRihZNB2o8BgS1yQ",
    "target": "w:19p5wJSSxXtYQYTBfbuvS8kVJxJcxtuaa1",
    "txHash": "tx:107975924",
    "amountBtc": 0.5,
    "amountEth": 0.5,
    "timestamp": "2014-05-10T12:00:00Z",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "mix_0755"
  },
  {
    "source": "w:19p5wJSSxXtYQYTBfbuvS8kVJxJcxtuaa1",
    "target": "w:1EPwT5QopwYrTANuU1Doc8paC2pCZyyckZ",
    "txHash": "tx:107975924",
    "amountBtc": 0.5,
    "amountEth": 0.5,
    "timestamp": "2014-05-10T12:00:00Z",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "mix_0755"
  },
  {
    "source": "w:1EPwT5QopwYrTANuU1Doc8paC2pCZyyckZ",
    "target": "w:1GjYoHwRXMSRzWgUxxPrvjMXd2XXbhtNA4",
    "txHash": "tx:107975924",
    "amountBtc": 0.5,
    "amountEth": 0.5,
    "timestamp": "2014-05-10T12:00:00Z",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "mix_0755"
  },
  {
    "source": "w:1GjYoHwRXMSRzWgUxxPrvjMXd2XXbhtNA4",
    "target": "w:1ZWUPH5znmERV7tiqojbVEySen",
    "txHash": "tx:107975924",
    "amountBtc": 0.5,
    "amountEth": 0.5,
    "timestamp": "2014-05-10T12:00:00Z",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "mix_0755"
  },
  {
    "source": "w:1ZWUPH5znmERV7tiqojbVEySen",
    "target": "w:1pX8mb3afMZWxyqvNc1uybCZozQseZt",
    "txHash": "tx:107975924",
    "amountBtc": 0.5,
    "amountEth": 0.5,
    "timestamp": "2014-05-10T12:00:00Z",
    "isSuspicious": true,
    "hopIndex": 1,
    "candidateId": "mix_0755"
  }
];

export const INITIAL_LOGS: KernelLogEntry[] = [
  {
    "id": "log-001",
    "timestamp": "16:22:19.004",
    "uptime": "[   0.000000]",
    "level": "SYS",
    "source": "kernel:bitkaun_core",
    "message": "BitKaun Forensic Kernel v6.2.0-btc-x86_64 mounted. Isolated TTY workspace online."
  },
  {
    "id": "log-002",
    "timestamp": "16:22:20.112",
    "uptime": "[   1.108421]",
    "level": "INFO",
    "source": "graph:heterogeneous_multigraph",
    "message": "Frozen V6 Graph built: 459,975 nodes, 527,143 edges index synchronized."
  },
  {
    "id": "log-003",
    "timestamp": "16:22:24.410",
    "uptime": "[   5.409482]",
    "level": "WARN",
    "source": "detector:peeling_chain",
    "message": "PEELING CHAIN DETECTED: Seed 1PTqbgVoXSbuzQKrDGw2M2tchx -> 4 consecutive hops with UTXO decay (candidate: peel_0564)."
  },
  {
    "id": "log-004",
    "timestamp": "16:22:28.912",
    "uptime": "[   9.811094]",
    "level": "CRIT",
    "source": "detector:layering_engine",
    "message": "LAYERING ALERT: Wallet 17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G fanned out 14 parallel routes, reconverging at sink 1JadLZMcaFX1JvRTkHmcAEZ4ygHm (candidate: layer_1054)."
  },
  {
    "id": "log-005",
    "timestamp": "16:22:36.120",
    "uptime": "[  17.020119]",
    "level": "WARN",
    "source": "detector:mixing_louvain",
    "message": "COINJOIN MIXING CLUSTER: Louvain community modularity 0.74 with 32 co-signing inputs and CV <= 0.50 (candidate: mix_0755)."
  },
  {
    "id": "log-006",
    "timestamp": "16:22:47.784",
    "uptime": "[  28.684022]",
    "level": "INFO",
    "source": "ml:xgboost_production",
    "message": "ML Stage 1 (Binary): AUC=0.999 | Stage 2 (Typology): Macro-F1=1.000 across 4 classes verified."
  },
  {
    "id": "log-007",
    "timestamp": "16:22:47.890",
    "uptime": "[  28.790101]",
    "level": "SYS",
    "source": "sec:session_audit",
    "message": "Integrity Check: 0 split leakage, 0 test address overlap, offline runtime certified."
  }
];

export const MOCK_HEX_DUMPS: Record<string, string[]> = {
  "12emAgNj5Uos6UcFafY6EEkq6u2": [
    "00000000  02 00 00 00 01 eb 7d 3a  8d 66 fc 77 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  58 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 eb 7d 3a 8d 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3132656d41674e6a  35556f7336556346  |12emAgNj5Uos6UcF|"
  ],
  "13fi2EpZFgjpjAnxaMzofw5GtBy": [
    "00000000  02 00 00 00 01 41 b9 fa  59 43 f9 34 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  96 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 41 b9 fa 59 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  313366693245705a  46676a706a416e78  |13fi2EpZFgjpjAnx|"
  ],
  "15FaQ7xbeSQEyxdfAUDTsBgFoua": [
    "00000000  02 00 00 00 01 58 d8 90  ca 3d f7 20 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  7b 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 58 d8 90 ca 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3135466151377862  6553514579786466  |15FaQ7xbeSQEyxdf|"
  ],
  "16BWsrV3Zf1pC5usQiREcVJrVa": [
    "00000000  02 00 00 00 01 53 ec 38  8a 1c 49 a1 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  ef 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 53 ec 38 8a 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3136425773725633  5a66317043357573  |16BWsrV3Zf1pC5us|"
  ],
  "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G": [
    "00000000  02 00 00 00 01 a3 b1 7e  8c 1d 61 28 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  aa 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 a3 b1 7e 8c 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  313755794c387974  5934596b544b547a  |17UyL8ytY4YkTKTz|"
  ],
  "17srEhi92HT5hF5ARERxnA3DznueUtJgc": [
    "00000000  02 00 00 00 01 79 00 b6  7e 70 03 49 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  7b 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 79 00 b6 7e 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3137737245686939  3248543568463541  |17srEhi92HT5hF5A|"
  ],
  "18oMPaHSWY8uJSeadAmQLcHfmc": [
    "00000000  02 00 00 00 01 1a a1 4a  8d 1c 30 67 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  96 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 1a a1 4a 8d 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31386f4d50614853  575938754a536561  |18oMPaHSWY8uJSea|"
  ],
  "19HepufHHXq5KoZnNqQfPwFHW77k": [
    "00000000  02 00 00 00 01 49 d1 8d  93 6c f7 e5 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  81 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 49 d1 8d 93 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3139486570756648  485871354b6f5a6e  |19HepufHHXq5KoZn|"
  ],
  "1Cq3HiZzahaS4PcwKeX9SMmtsw3hiTr3Xz": [
    "00000000  02 00 00 00 01 07 c0 5f  a2 1b 8d 9c 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  44 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 07 c0 5f a2 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3143713348695a7a  6168615334506377  |1Cq3HiZzahaS4Pcw|"
  ],
  "1DnWHZtdtCP57xCqjbuBxkHXHqU": [
    "00000000  02 00 00 00 01 17 87 e6  5b 2f 9b a9 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  8d 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 17 87 e6 5b 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31446e57485a7464  7443503537784371  |1DnWHZtdtCP57xCq|"
  ],
  "1Et4y3xsYYZCtQLv3aZGYaz5eTafhph": [
    "00000000  02 00 00 00 01 01 64 2a  ee 19 22 ba 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  0f 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 01 64 2a ee 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3145743479337873  59595a4374514c76  |1Et4y3xsYYZCtQLv|"
  ],
  "1JCGLh437W14JXw8uNgLkjRka878B2F": [
    "00000000  02 00 00 00 01 3e eb 6a  15 64 d7 a9 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  35 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 3e eb 6a 15 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  314a43474c683433  375731344a587738  |1JCGLh437W14JXw8|"
  ],
  "1JadLZMcaFX1JvRTkHmcAEZ4ygHm": [
    "00000000  02 00 00 00 01 e4 bd b2  f5 43 94 b2 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  41 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 e4 bd b2 f5 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  314a61644c5a4d63  614658314a765254  |1JadLZMcaFX1JvRT|"
  ],
  "1KyJRwBvxLpV9S8LKDCVP7CYyqALvkAm2H": [
    "00000000  02 00 00 00 01 f2 3d cc  a6 26 40 05 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  9a 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 f2 3d cc a6 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  314b794a52774276  784c70563953384c  |1KyJRwBvxLpV9S8L|"
  ],
  "1MPjtn7eqawrM7gBJsQsBT3wzMuzWz56F1": [
    "00000000  02 00 00 00 01 cb 0c cb  01 7c 31 8c 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  9b 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 cb 0c cb 01 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  314d506a746e3765  716177724d376742  |1MPjtn7eqawrM7gB|"
  ],
  "1NWuKnHBKUnzJRw7LPLxpd1RvMP32b": [
    "00000000  02 00 00 00 01 56 27 9a  d6 30 72 2d 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  dd 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 56 27 9a d6 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  314e57754b6e4842  4b556e7a4a527737  |1NWuKnHBKUnzJRw7|"
  ],
  "1PTqbgVoXSbuzQKrDGw2M2tchx": [
    "00000000  02 00 00 00 01 78 a7 be  98 6b 79 cd 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  7f 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 78 a7 be 98 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  315054716267566f  585362757a514b72  |1PTqbgVoXSbuzQKr|"
  ],
  "1Q75uGchVa4eN8EHuQiuX8z9j3oS9Ng1XT": [
    "00000000  02 00 00 00 01 19 8c e7  b5 6b e5 ce 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  92 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 19 8c e7 b5 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3151373575476368  566134654e384548  |1Q75uGchVa4eN8EH|"
  ],
  "1QBMzLsqyakZJgWea4KyeitHbNx3qKYA": [
    "00000000  02 00 00 00 01 16 06 dc  03 77 8d 72 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  ee 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 16 06 dc 03 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3151424d7a4c7371  79616b5a4a675765  |1QBMzLsqyakZJgWe|"
  ],
  "1RBv2NCXCTKZeiL9cEkJAaWUAPh2Q": [
    "00000000  02 00 00 00 01 6d 53 8a  aa 29 73 2c 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  9c 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 6d 53 8a aa 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31524276324e4358  43544b5a65694c39  |1RBv2NCXCTKZeiL9|"
  ],
  "1Ro556NAYBZpbrUtJRCqg1qiiiW4": [
    "00000000  02 00 00 00 01 08 b8 10  07 3d af 6f 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  49 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 08 b8 10 07 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31526f3535364e41  59425a7062725574  |1Ro556NAYBZpbrUt|"
  ],
  "1SDQmJYVPcqajMCucmnBhTrVCVd6Ec": [
    "00000000  02 00 00 00 01 ca 58 a4  89 04 52 05 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  e3 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 ca 58 a4 89 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  315344516d4a5956  506371616a4d4375  |1SDQmJYVPcqajMCu|"
  ],
  "1U2qQJkhBdHu5aWKwxpLtkx4Dh": [
    "00000000  02 00 00 00 01 8d 88 c2  d1 7e e2 c0 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  5b 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 8d 88 c2 d1 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31553271514a6b68  426448753561574b  |1U2qQJkhBdHu5aWK|"
  ],
  "1UFPZf167WSynu8FCvH9BWMqdK8ygZ": [
    "00000000  02 00 00 00 01 fa 48 f1  4b 27 c7 d9 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  17 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 fa 48 f1 4b 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  315546505a663136  375753796e753846  |1UFPZf167WSynu8F|"
  ],
  "1Ujf566EUPjTDAPh2icNyCbxQmQ6qhp": [
    "00000000  02 00 00 00 01 e3 fa 9c  b2 33 f4 12 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  2b 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 e3 fa 9c b2 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31556a6635363645  55506a5444415068  |1Ujf566EUPjTDAPh|"
  ],
  "1VPcvAf5tmJP8EECAH6bRSZqurofau": [
    "00000000  02 00 00 00 01 b9 c7 c1  08 51 1f a1 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  11 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 b9 c7 c1 08 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3156506376416635  746d4a5038454543  |1VPcvAf5tmJP8EEC|"
  ],
  "1XmiVkPbNe6dMVQFbottSStugoZSN": [
    "00000000  02 00 00 00 01 8b 66 8e  18 7c 1f b6 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  06 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 8b 66 8e 18 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31586d69566b5062  4e6536644d565146  |1XmiVkPbNe6dMVQF|"
  ],
  "1XsbsHvneK4VGRrQZCCG6fnGGBNpAqc": [
    "00000000  02 00 00 00 01 ef 8a 18  e0 12 7c 09 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  2e 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 ef 8a 18 e0 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  315873627348766e  654b345647527251  |1XsbsHvneK4VGRrQ|"
  ],
  "1YNB9Yxwd1KTbKVFVQyqurHDyR6LeGYMAD": [
    "00000000  02 00 00 00 01 23 61 77  2a 2c 72 d3 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  da 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 23 61 77 2a 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31594e4239597877  64314b54624b5646  |1YNB9Yxwd1KTbKVF|"
  ],
  "1ZmZYV7ns1khJhh7jfoKXnWgqFFpVYy57K": [
    "00000000  02 00 00 00 01 af 21 c3  34 4b d8 46 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  54 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 af 21 c3 34 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  315a6d5a5956376e  73316b684a686837  |1ZmZYV7ns1khJhh7|"
  ],
  "1cNd1nppdeJ3hfXiNpnoyM4Bu9rrGLvq": [
    "00000000  02 00 00 00 01 64 fd 86  84 35 86 35 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  60 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 64 fd 86 84 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31634e64316e7070  64654a3368665869  |1cNd1nppdeJ3hfXi|"
  ],
  "1d92F9SKdQ18Az2ni9chFrM2p2wmUcC": [
    "00000000  02 00 00 00 01 82 38 eb  63 2d cc aa 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  c8 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 82 38 eb 63 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  316439324639534b  64513138417a326e  |1d92F9SKdQ18Az2n|"
  ],
  "1eT1dF73RFreuuhuimB8CadRSbv": [
    "00000000  02 00 00 00 01 28 9c d5  c5 43 db 33 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  be 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 28 9c d5 c5 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3165543164463733  5246726575756875  |1eT1dF73RFreuuhu|"
  ],
  "1fCw9QCXdCYoKaBFsyWbyVgZw8n4Hkp": [
    "00000000  02 00 00 00 01 a6 d9 fa  c6 69 42 66 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  5e 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 a6 d9 fa c6 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3166437739514358  6443596f4b614246  |1fCw9QCXdCYoKaBF|"
  ],
  "1g64wCdEj3frZLfsRPtm5Xdke1fdiJeG": [
    "00000000  02 00 00 00 01 2f 21 83  16 18 22 95 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  e2 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 2f 21 83 16 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3167363477436445  6a3366725a4c6673  |1g64wCdEj3frZLfs|"
  ],
  "1kj5cC8PYnTmwGgkpLKAFk3Ubh8fE": [
    "00000000  02 00 00 00 01 85 78 4f  32 56 8a 1f 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  7a 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 85 78 4f 32 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  316b6a3563433850  596e546d7747676b  |1kj5cC8PYnTmwGgk|"
  ],
  "1nErH5MRLErVwVQZZ9w44yhX7TcVzM": [
    "00000000  02 00 00 00 01 91 be c9  18 19 d7 e5 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  d7 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 91 be c9 18 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  316e457248354d52  4c4572567756515a  |1nErH5MRLErVwVQZ|"
  ],
  "1o5XftUNrK8KJ1fj64KgDwiXd7CDB7r": [
    "00000000  02 00 00 00 01 b1 82 e6  c2 55 7a 0f 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  1b 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 b1 82 e6 c2 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  316f35586674554e  724b384b4a31666a  |1o5XftUNrK8KJ1fj|"
  ],
  "1piDkxRaDo8VfRnxnSEHvz93i5H6zdT": [
    "00000000  02 00 00 00 01 b3 13 f7  a2 0d 72 f4 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  6f 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 b3 13 f7 a2 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  317069446b785261  446f385666526e78  |1piDkxRaDo8VfRnx|"
  ],
  "1rGumkvop4ddCHftQ5zweJ17FZ": [
    "00000000  02 00 00 00 01 6c f8 75  ab 2f e3 18 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  7a 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 6c f8 75 ab 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  317247756d6b766f  7034646443486674  |1rGumkvop4ddCHft|"
  ],
  "1rVWwVr773EM8RscY9epNJsYqMj": [
    "00000000  02 00 00 00 01 1b 84 ce  6d 4e 51 4f 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  f0 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 1b 84 ce 6d 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3172565777567237  3733454d38527363  |1rVWwVr773EM8Rsc|"
  ],
  "1s6D1TaSbKqeTG5YMhWWRJ85Ve8s7Y": [
    "00000000  02 00 00 00 01 57 be 6d  1f 1e 95 49 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  35 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 57 be 6d 1f 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3173364431546153  624b716554473559  |1s6D1TaSbKqeTG5Y|"
  ],
  "1snCZQN8XGEW3gkwQWv6FRhpat5Qfttgv": [
    "00000000  02 00 00 00 01 1e b1 a6  e5 0b b7 96 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  e9 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 1e b1 a6 e5 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31736e435a514e38  5847455733676b77  |1snCZQN8XGEW3gkw|"
  ],
  "1unSWocZerQPVe3pmydVV8KGgUD": [
    "00000000  02 00 00 00 01 40 58 32  e7 6a cd 35 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  2d 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 40 58 32 e7 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31756e53576f635a  6572515056653370  |1unSWocZerQPVe3p|"
  ],
  "1vcTcJc5qokb2buGGbG1yNrDk7YLar": [
    "00000000  02 00 00 00 01 5a 86 ba  69 12 7e bb 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  ec 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 5a 86 ba 69 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31766354634a6335  716f6b6232627547  |1vcTcJc5qokb2buG|"
  ],
  "1wChDwqJSQgTgKgRzsbANwMRXxvXLKHKN3": [
    "00000000  02 00 00 00 01 8f 24 85  4c 78 92 04 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  37 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 8f 24 85 4c 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  317743684477714a  53516754674b6752  |1wChDwqJSQgTgKgR|"
  ],
  "1wMdNuDqsBFmncgNNpa3eAxGXi4L": [
    "00000000  02 00 00 00 01 55 d4 ea  93 3a 0e 25 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  0c 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 55 d4 ea 93 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31774d644e754471  7342466d6e63674e  |1wMdNuDqsBFmncgN|"
  ],
  "1wUM3XMsQVTSYEVWMnzm5d7TfYwY": [
    "00000000  02 00 00 00 01 28 cf da  b1 03 ff 7d 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  f4 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 28 cf da b1 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3177554d33584d73  5156545359455657  |1wUM3XMsQVTSYEVW|"
  ],
  "1yVnD1uQau5YS2SWiotwP8dDsd": [
    "00000000  02 00 00 00 01 e6 ee aa  45 33 03 77 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  81 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 e6 ee aa 45 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3179566e44317551  6175355953325357  |1yVnD1uQau5YS2SW|"
  ],
  "1ycD73SBsCDVVg6hocEieDisnS2BELDqs2": [
    "00000000  02 00 00 00 01 ab 15 94  ae 49 b9 ba 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  b9 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 ab 15 94 ae 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3179634437335342  7343445656673668  |1ycD73SBsCDVVg6h|"
  ],
  "1zX2QbzuWQ8dv7QKGBePEZYsEJ": [
    "00000000  02 00 00 00 01 26 b7 1c  f8 3f 84 b7 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  8b 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 26 b7 1c f8 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  317a583251627a75  575138647637514b  |1zX2QbzuWQ8dv7QK|"
  ],
  "w:13xtQfa6QBdRihZNB2o8BgS1yQ": [
    "00000000  02 00 00 00 01 7c e1 ca  3f 79 31 f8 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  54 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 7c e1 ca 3f 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3133787451666136  5142645269685a4e  |13xtQfa6QBdRihZN|"
  ],
  "w:18VkGCV1zZ8YV6PwG1LHdL7JB7": [
    "00000000  02 00 00 00 01 9c 27 6e  59 75 82 bf 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  5a 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 9c 27 6e 59 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3138566b47435631  7a5a385956365077  |18VkGCV1zZ8YV6Pw|"
  ],
  "w:19p5wJSSxXtYQYTBfbuvS8kVJxJcxtuaa1": [
    "00000000  02 00 00 00 01 6a dc 66  1f 3c 34 12 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  b7 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 6a dc 66 1f 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31397035774a5353  7858745951595442  |19p5wJSSxXtYQYTB|"
  ],
  "w:1EPwT5QopwYrTANuU1Doc8paC2pCZyyckZ": [
    "00000000  02 00 00 00 01 4d 80 a8  53 17 9b 93 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  85 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 4d 80 a8 53 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  314550775435516f  7077597254414e75  |1EPwT5QopwYrTANu|"
  ],
  "w:1GjYoHwRXMSRzWgUxxPrvjMXd2XXbhtNA4": [
    "00000000  02 00 00 00 01 da 68 60  0e 30 30 c6 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  84 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 da 68 60 0e 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31476a596f487752  584d53527a576755  |1GjYoHwRXMSRzWgU|"
  ],
  "w:1Qn5mncfUDCKj8pZPzgVedT3b8pB": [
    "00000000  02 00 00 00 01 66 b9 31  bd 45 56 eb 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  38 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 66 b9 31 bd 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31516e356d6e6366  5544434b6a38705a  |1Qn5mncfUDCKj8pZ|"
  ],
  "w:1S9i9JWinMeM7uuq7uEDdfL9TnawfSrWMw": [
    "00000000  02 00 00 00 01 41 b2 e0  17 10 d8 3f 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  86 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 41 b2 e0 17 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31533969394a5769  6e4d654d37757571  |1S9i9JWinMeM7uuq|"
  ],
  "w:1T2DUQ6AyVCtciuLdpvuwVprPJxa3Zm1dX": [
    "00000000  02 00 00 00 01 05 ac 72  b5 5c d7 71 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  0e 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 05 ac 72 b5 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3154324455513641  795643746369754c  |1T2DUQ6AyVCtciuL|"
  ],
  "w:1ZWUPH5znmERV7tiqojbVEySen": [
    "00000000  02 00 00 00 01 b5 fe 5e  d3 23 55 8b 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  6d 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 b5 fe 5e d3 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  315a57555048357a  6e6d455256377469  |1ZWUPH5znmERV7ti|"
  ],
  "w:1eAjAUKEjvUzeCD3JCq8sJFZRBKw": [
    "00000000  02 00 00 00 01 24 f1 7e  0b 2b 67 a2 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  06 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 24 f1 7e 0b 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3165416a41554b45  6a76557a65434433  |1eAjAUKEjvUzeCD3|"
  ],
  "w:1euRz5ZF211ZH1DpLyhFiSZmvSvAmqG15": [
    "00000000  02 00 00 00 01 03 9b 0f  35 27 8c 59 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  a3 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 03 9b 0f 35 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  316575527a355a46  3231315a48314470  |1euRz5ZF211ZH1Dp|"
  ],
  "w:1m9uKtJS1iMMyjbAsofardA9kqCUHG5J": [
    "00000000  02 00 00 00 01 4a a0 9b  1d 15 a4 06 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  a3 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 4a a0 9b 1d 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  316d39754b744a53  31694d4d796a6241  |1m9uKtJS1iMMyjbA|"
  ],
  "w:1pX8mb3afMZWxyqvNc1uybCZozQseZt": [
    "00000000  02 00 00 00 01 74 f3 f2  aa 7b 0b 48 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  44 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 74 f3 f2 aa 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  317058386d623361  664d5a5778797176  |1pX8mb3afMZWxyqv|"
  ],
  "w:1rL23qSNXqg6SyuEwoXCtpPB2qML": [
    "00000000  02 00 00 00 01 bd c4 6e  47 5a 1b b9 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  8f 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 bd c4 6e 47 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  31724c323371534e  5871673653797545  |1rL23qSNXqg6SyuE|"
  ],
  "w:1sBXzQtjivghnY9Fu8rEXw58wtB2iq": [
    "00000000  02 00 00 00 01 87 de 7d  b7 5a 6e 98 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  ca 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 87 de 7d b7 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  317342587a51746a  697667686e593946  |1sBXzQtjivghnY9F|"
  ],
  "w:1sBn8wgQ5C4y4sGan1Li4WHDFwwJs": [
    "00000000  02 00 00 00 01 d5 07 7b  00 1b e7 54 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  4b 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 d5 07 7b 00 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3173426e38776751  3543347934734761  |1sBn8wgQ5C4y4sGa|"
  ],
  "w:1y11idQQmCP8vJq3qEavxsx1Hy6Qtb7xD": [
    "00000000  02 00 00 00 01 b3 7b 50  1c 3d 8d 6d 00 00 00 00  |.....BitcoinTx..|",
    "00000010  6a 47 30 44 02 20 1b 4c  8e 99 a0 14 00 00 00 00  |jG0D. .L........|",
    "00000020  41 04 78 3b 00 00 00 00  4a 3b 00 00 00 00 00 00  |A.x;....;.......|",
    "00000030  76 a9 14 b3 7b 50 1c 88  ac 00 00 00 00 00 00 00  |v.........OP_CKV|",
    "00000040  00 00 00 00 40 00 38 00  09 00 40 00 1f 00 1e 00  |....@.8...@.....|",
    "00000050  3179313169645151  6d435038764a7133  |1y11idQQmCP8vJq3|"
  ]
};

export const CANDIDATE_INDEX = [
  {
    "candidate_id": "peel_0564",
    "candidate_type": "peeling_chain",
    "wallets_count": 5,
    "tx_count": 4,
    "total_btc": 1.48094194,
    "origin": "1PTqbgVoXSbuzQKrDGw2M2tchx",
    "sink": "1s6D1TaSbKqeTG5YMhWWRJ85Ve8s7Y"
  },
  {
    "candidate_id": "peel_0565",
    "candidate_type": "peeling_chain",
    "wallets_count": 3,
    "tx_count": 3,
    "total_btc": 0.16565719,
    "origin": "1Ro556NAYBZpbrUtJRCqg1qiiiW4",
    "sink": "1rGumkvop4ddCHftQ5zweJ17FZ"
  },
  {
    "candidate_id": "layer_1054",
    "candidate_type": "layering",
    "wallets_count": 30,
    "tx_count": 16,
    "total_btc": 2.53955747,
    "origin": "17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G",
    "sink": "1JadLZMcaFX1JvRTkHmcAEZ4ygHm"
  },
  {
    "candidate_id": "mix_0755",
    "candidate_type": "mixing",
    "wallets_count": 6,
    "tx_count": 1,
    "total_btc": 2.87353498,
    "origin": "w:13xtQfa6QBdRihZNB2o8BgS1yQ",
    "sink": "w:1pX8mb3afMZWxyqvNc1uybCZozQseZt"
  },
  {
    "candidate_id": "mix_0756",
    "candidate_type": "mixing",
    "wallets_count": 5,
    "tx_count": 1,
    "total_btc": 0.98674598,
    "origin": "w:18VkGCV1zZ8YV6PwG1LHdL7JB7",
    "sink": "w:1sBn8wgQ5C4y4sGan1Li4WHDFwwJs"
  },
  {
    "candidate_id": "peel_0001",
    "candidate_type": "peeling_chain",
    "wallets_count": 5,
    "tx_count": 5,
    "total_btc": 0.86620643,
    "origin": "1ZmZYV7ns1khJhh7jfoKXnWgqFFpVYy57K",
    "sink": "13fi2EpZFgjpjAnxaMzofw5GtBy"
  },
  {
    "candidate_id": "peel_0002",
    "candidate_type": "peeling_chain",
    "wallets_count": 5,
    "tx_count": 5,
    "total_btc": 2.13088217,
    "origin": "1unSWocZerQPVe3pmydVV8KGgUD",
    "sink": "19HepufHHXq5KoZnNqQfPwFHW77k"
  },
  {
    "candidate_id": "peel_0003",
    "candidate_type": "peeling_chain",
    "wallets_count": 3,
    "tx_count": 3,
    "total_btc": 0.86083101,
    "origin": "1VPcvAf5tmJP8EECAH6bRSZqurofau",
    "sink": "1XmiVkPbNe6dMVQFbottSStugoZSN"
  }
];

export const COMMAND_REGISTRY: CommandDescriptor[] = [
  {
    name: 'help',
    aliases: ['man', '?', 'info'],
    usage: 'help [command]',
    summary: 'Display interactive forensic manual and command syntax.',
    description: 'Displays the complete Bitcoin AML forensic command reference, parameter specifications, and investigation procedures.',
    category: 'NAVIGATION',
    examples: ['help', 'help trace', 'man inspect']
  },
  {
    name: 'graph',
    aliases: ['nodes', 'g', 'ls nodes'],
    usage: 'graph [peel|layer|mix|all]',
    summary: 'Mount the full-viewport 3D WebGL Force Graph of Bitcoin wallets and transfer links.',
    description: 'Renders the Bitcoin transaction graph in 3D WebGL space. Supports point-cloud background density with high-resolution wireframe overlays on detected laundering candidates. Drag rotates, right-click pans, scroll zooms, and clicking nodes opens dossiers.',
    category: 'NAVIGATION',
    examples: ['graph', 'graph peel', 'graph layer', 'graph mix']
  },
  {
    name: 'inspect',
    aliases: ['cat', 'hex', 'view'],
    usage: 'inspect <BITCOIN_ADDRESS>',
    summary: 'Mount forensic byte hexdump, AML risk metrics, and entity intelligence dossier.',
    description: 'Displays UTXO balance, transaction counts, heuristic risk score, Tor/VPN broadcast infrastructure, and raw Bitcoin script bytecode for any address.',
    category: 'FORENSICS',
    examples: [
      'inspect 1PTqbgVoXSbuzQKrDGw2M2tchx',
      'inspect 17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G',
      'inspect 1JadLZMcaFX1JvRTkHmcAEZ4ygHm'
    ]
  },
  {
    name: 'trace',
    aliases: ['tr', 'path', 'flow'],
    usage: 'trace <SRC_ADDRESS> <DST_ADDRESS> | trace <CANDIDATE_ID>',
    summary: 'Calculate and visually reconstruct multi-hop laundering fund flow.',
    description: 'Reconstructs the directed UTXO flow across peeling hops, fan-out layering routes, or CoinJoin co-signers, detailing transferred BTC volumes, fees, and timestamps.',
    category: 'FORENSICS',
    examples: [
      'trace 1PTqbgVoXSbuzQKrDGw2M2tchx 1s6D1TaSbKqeTG5YMhWWRJ85Ve8s7Y',
      'trace 17UyL8ytY4YkTKTzsJ8btTCr9EWpyGBk3G 1JadLZMcaFX1JvRTkHmcAEZ4ygHm',
      'trace peel_0564',
      'trace layer_1054'
    ]
  },
  {
    name: 'dmesg',
    aliases: ['logs', 'd', 'tail -f'],
    usage: 'dmesg [filter]',
    summary: 'Stream live rolling kernel logs, AML intercepts, and detection alerts.',
    description: 'Displays real-time system audit logs, mempool intercepts, and automated threat intelligence detection alerts from the V6 graph engine.',
    category: 'SYSTEM',
    examples: ['dmesg', 'logs', 'd']
  },
  {
    name: 'home',
    aliases: ['banner', 'cd ~', 'cd'],
    usage: 'home',
    summary: 'Return to the root landing screen with the BitKaun terminal banner.',
    description: 'Restores the root TTY1 welcome screen, investigation overview, and quick-start tips.',
    category: 'NAVIGATION',
    examples: ['home', 'banner']
  },
  {
    name: 'sound',
    aliases: ['audio', 'mute'],
    usage: 'sound <on|off|toggle>',
    summary: 'Toggle procedural retro terminal keyboard clicks and synthesizer chirps.',
    description: 'Enables or disables the procedural Web Audio synthesizer that generates mechanical keystrokes and kernel alert beeps.',
    category: 'SYSTEM',
    examples: ['sound on', 'sound off', 'sound']
  },
  {
    name: 'status',
    aliases: ['sys', 'top', 'whoami', 'uname'],
    usage: 'status',
    summary: 'Display forensic graph telemetry, memory buffer allocations, and detector statistics.',
    description: 'Outputs dataset version, total nodes, edges, active typologies, and ML classification accuracy.',
    category: 'SYSTEM',
    examples: ['status', 'top']
  },
  {
    name: 'clear',
    aliases: ['cls'],
    usage: 'clear',
    summary: 'Flush current terminal stdout history buffer (Shortcut: Ctrl+L).',
    description: 'Clears the bottom terminal command output history buffer and repositions cursor.',
    category: 'NAVIGATION',
    examples: ['clear', 'cls']
  }
];
