# API Contract — Bitcoin AML Forensics Platform

> **Source-of-Truth Note:** Backend (P6) and Frontend (P1/P2) both build against this contract. Update this document **BEFORE** changing any endpoint signature, parameter, or response shape.

---

## 1. Endpoint Summary

All API endpoints strictly use field names and types specified in [DATA_DICTIONARY.md](../DATA_DICTIONARY.md).

| Method | Route | Description | Primary Owners |
|---|---|---|---|
| `GET` | `/health` | System telemetry, loaded transaction count, unique wallets, uptime. | P6 (Backend) |
| `GET` | `/entity/{address}` | Retrieve address metadata, transaction counts, and exchange flag. | P6 (Backend), P1/P2 (Frontend) |
| `GET` | `/transaction/{txid}` | Retrieve full transaction details (on-chain multi-I/O UTXO + network telemetry). | P6 (Backend), P1/P2 (Frontend) |
| `GET` | `/graph/{scenario_id}` | Retrieve graph nodes (`Wallet`, `Transaction`, `IP`) and edges (`SENT`, `RECEIVED`, `BROADCAST`) for a scenario. | P4 (Graph), P6 (Backend), P2 (Graph UI) |
| `GET` | `/trace` | Compute multi-hop shortest path between source and destination wallets. | P6 (Backend), P1/P2 (Frontend) |
| `GET` | `/alerts` | Retrieve prioritized list of forensic candidate alerts with ML predictions and explanations. | P5 (ML), P6 (Backend), P1 (Alert Feed) |
| `GET` | `/alerts/{candidate_id}/evidence` | Retrieve full forensic evidence dossier and feature attribution breakdown for a specific candidate. | P5 (ML/SHAP), P6 (Backend), P1/P2 (Frontend) |

---

## 2. Detailed Endpoint Specifications

### 2.1 `GET /health`

Returns server uptime, loaded transaction status, and memory store diagnostics.

- **Response Status:** `200 OK`

#### Example Response (JSON)
```json
{
  "status": "ONLINE",
  "app_name": "BitKaun AML Forensics API",
  "version": "2.0.0",
  "loaded_transactions": 82078,
  "unique_scenarios": 17613,
  "unique_wallets": 284401,
  "uptime_seconds": 12.45
}
```

---

### 2.2 `GET /entity/{address}`

Retrieves profile details for a given Bitcoin address.

- **URL Parameter:** `address` (string, Base58 Bitcoin address)
- **Response Status:** `200 OK` (or `404 Not Found` if address has no recorded activity)

#### Example Request
```http
GET /entity/1PZDhrao8CqYBnFzEk67TbPxX8MxbKjhmh HTTP/1.1
Host: localhost:8000
```

#### Example Response (JSON)
```json
{
  "address": "1PZDhrao8CqYBnFzEk67TbPxX8MxbKjhmh",
  "is_licit_exchange": false,
  "total_received_btc": 14.52918000,
  "total_sent_btc": 14.52882892,
  "tx_count": 8,
  "first_seen": "2014-03-15 09:22:41",
  "last_seen": "2014-03-15 11:45:10",
  "associated_scenarios": [
    "peel_001"
  ]
}
```

---

### 2.3 `GET /transaction/{txid}`

Retrieves the combined dual-layer ledger record and P2P telemetry for a specific `txid`.

- **URL Parameter:** `txid` (int64 integer ID)
- **Response Status:** `200 OK` (or `404 Not Found`)

#### Example Request
```http
GET /transaction/58234917 HTTP/1.1
Host: localhost:8000
```

#### Example Response (JSON)
```json
{
  "txid": 58234917,
  "timestamp": "2014-03-15 09:22:41",
  "input_addresses": [
    "12dhqUGwzF6c6eW5F7DkyXyqBmW1"
  ],
  "output_addresses": [
    "1EcgU6KKSdjtWmXzy5W3EX34ibCoH",
    "1PZDhrao8CqYBnFzEk67TbPxX8MxbKjhmh"
  ],
  "input_amounts": [
    0.26361416
  ],
  "output_amounts": [
    0.05260000,
    0.21066308
  ],
  "fee_btc": 0.00035108,
  "script_type": "P2PKH",
  "scenario_id": "peel_001",
  "network": {
    "relay_timestamp": "2014-03-15 09:22:40.812",
    "relay_ip": "38.148.127.142",
    "relay_port": 8333,
    "node_type": "residential",
    "country_code": "IN",
    "asn": "AS55836",
    "isp": "Reliance Jio Infocomm",
    "protocol_version": 70015,
    "user_agent": "/Satoshi:22.0.0/",
    "propagation_delta_ms": 188
  }
}
```

---

### 2.4 `GET /graph/{scenario_id}`

Retrieves the heterogeneous graph representation for an entire scenario or cluster, adhering to Section 7 of `DATA_DICTIONARY.md`.

- **URL Parameter:** `scenario_id` (string, e.g., `peel_001`, `layer_014`, `mix_003`)
- **Response Status:** `200 OK`

#### Example Request
```http
GET /graph/peel_001 HTTP/1.1
Host: localhost:8000
```

#### Example Response (JSON)
```json
{
  "scenario_id": "peel_001",
  "nodes": [
    {
      "id": "12dhqUGwzF6c6eW5F7DkyXyqBmW1",
      "type": "Wallet",
      "properties": {
        "address": "12dhqUGwzF6c6eW5F7DkyXyqBmW1",
        "is_licit_exchange": false
      }
    },
    {
      "id": "1EcgU6KKSdjtWmXzy5W3EX34ibCoH",
      "type": "Wallet",
      "properties": {
        "address": "1EcgU6KKSdjtWmXzy5W3EX34ibCoH",
        "is_licit_exchange": false
      }
    },
    {
      "id": "1PZDhrao8CqYBnFzEk67TbPxX8MxbKjhmh",
      "type": "Wallet",
      "properties": {
        "address": "1PZDhrao8CqYBnFzEk67TbPxX8MxbKjhmh",
        "is_licit_exchange": false
      }
    },
    {
      "id": "tx_58234917",
      "type": "Transaction",
      "properties": {
        "txid": 58234917,
        "timestamp": "2014-03-15 09:22:41",
        "fee_btc": 0.00035108,
        "script_type": "P2PKH",
        "scenario_id": "peel_001"
      }
    },
    {
      "id": "ip_38.148.127.142",
      "type": "IP",
      "properties": {
        "relay_ip": "38.148.127.142",
        "country_code": "IN",
        "asn": "AS55836",
        "isp": "Reliance Jio Infocomm",
        "node_type": "residential",
        "relay_port": 8333
      }
    }
  ],
  "edges": [
    {
      "id": "edge_sent_12dhq_58234917",
      "source": "12dhqUGwzF6c6eW5F7DkyXyqBmW1",
      "target": "tx_58234917",
      "type": "SENT",
      "properties": {
        "amount_btc": 0.26361416
      }
    },
    {
      "id": "edge_rec_58234917_1Ecg",
      "source": "tx_58234917",
      "target": "1EcgU6KKSdjtWmXzy5W3EX34ibCoH",
      "type": "RECEIVED",
      "properties": {
        "amount_btc": 0.05260000
      }
    },
    {
      "id": "edge_rec_58234917_1PZD",
      "source": "tx_58234917",
      "target": "1PZDhrao8CqYBnFzEk67TbPxX8MxbKjhmh",
      "type": "RECEIVED",
      "properties": {
        "amount_btc": 0.21066308
      }
    },
    {
      "id": "edge_broad_38_58234917",
      "source": "ip_38.148.127.142",
      "target": "tx_58234917",
      "type": "BROADCAST",
      "properties": {
        "relay_timestamp": "2014-03-15 09:22:40.812",
        "relay_port": 8333,
        "user_agent": "/Satoshi:22.0.0/"
      }
    }
  ]
}
```

---

### 2.5 `GET /trace`

Traces the multi-hop transaction flow path between a source address and destination address.

- **Query Parameters:**
  - `src` (string, required): Source Bitcoin address
  - `dst` (string, required): Destination Bitcoin address
  - `max_depth` (int, default: 6): Maximum hop search depth
- **Response Status:** `200 OK`

#### Example Request
```http
GET /trace?src=12dhqUGwzF6c6eW5F7DkyXyqBmW1&dst=1EcgU6KKSdjtWmXzy5W3EX34ibCoH&max_depth=4 HTTP/1.1
Host: localhost:8000
```

#### Example Response (JSON)
```json
{
  "source_address": "12dhqUGwzF6c6eW5F7DkyXyqBmW1",
  "destination_address": "1EcgU6KKSdjtWmXzy5W3EX34ibCoH",
  "path_found": true,
  "hop_count": 2,
  "total_transferred_btc": 0.26326308,
  "hops": [
    {
      "hop_index": 1,
      "from_wallet": "12dhqUGwzF6c6eW5F7DkyXyqBmW1",
      "to_wallet": "1PZDhrao8CqYBnFzEk67TbPxX8MxbKjhmh",
      "txid": 58234917,
      "amount_btc": 0.21066308,
      "timestamp": "2014-03-15 09:22:41",
      "flagged_typology": "peeling_chain"
    },
    {
      "hop_index": 2,
      "from_wallet": "1PZDhrao8CqYBnFzEk67TbPxX8MxbKjhmh",
      "to_wallet": "1EcgU6KKSdjtWmXzy5W3EX34ibCoH",
      "txid": 58234918,
      "amount_btc": 0.05260000,
      "timestamp": "2014-03-15 09:22:42",
      "flagged_typology": "peeling_chain"
    }
  ]
}
```

---

### 2.6 `GET /alerts`

Retrieves a ranked list of candidate alerts identified by the graph detection heuristics and classified by the ML engine.

- **Query Parameters (Optional):**
  - `limit` (int, default: 50)
  - `min_confidence` (float, default: 0.50)
  - `pattern_type` (string enum: `ransomware`, `peeling_chain`, `layering`, `mixing`)
- **Response Status:** `200 OK`

#### Example Request
```http
GET /alerts?min_confidence=0.80&limit=10 HTTP/1.1
Host: localhost:8000
```

#### Example Response (JSON)
```json
{
  "total_alerts": 34,
  "alerts": [
    {
      "candidate_id": "cand_peel_001_seq01",
      "scenario_id": "peel_001",
      "predicted_pattern_type": "peeling_chain",
      "confidence": 0.942,
      "severity": "CRITICAL",
      "explanation": "Sequential 1-in-2-out transactions peeling small outputs (avg 0.05 BTC) with change reuse across 5 consecutive hops via bulletproof infrastructure (AS210644).",
      "primary_wallet": "12dhqUGwzF6c6eW5F7DkyXyqBmW1",
      "member_txids": [
        58234917,
        58234918,
        58234922,
        58234925,
        58234931
      ],
      "member_wallets": [
        "12dhqUGwzF6c6eW5F7DkyXyqBmW1",
        "1EcgU6KKSdjtWmXzy5W3EX34ibCoH",
        "1PZDhrao8CqYBnFzEk67TbPxX8MxbKjhmh",
        "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
      ],
      "detected_at": "2026-09-03T04:15:00Z"
    },
    {
      "candidate_id": "cand_layer_014_seq02",
      "scenario_id": "layer_014",
      "predicted_pattern_type": "layering",
      "confidence": 0.887,
      "severity": "HIGH",
      "explanation": "Rapid fan-out from single UTXO into 8 intermediate addresses followed by 8-to-1 fan-in reconvergence within 12 minutes.",
      "primary_wallet": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
      "member_txids": [
        61092834,
        61092835,
        61092840
      ],
      "member_wallets": [
        "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
        "13AM4VW2dhxYgXeQepoHkHSQuy6NgaEb94"
      ],
      "detected_at": "2026-09-03T04:12:10Z"
    }
  ]
}
```

---

### 2.7 `GET /alerts/{candidate_id}/evidence`

Retrieves deep forensic evidence, SHAP feature attributions, and transaction telemetry breakdown for an alert candidate.

- **URL Parameter:** `candidate_id` (string)
- **Response Status:** `200 OK` (or `404 Not Found`)

#### Example Request
```http
GET /alerts/cand_peel_001_seq01/evidence HTTP/1.1
Host: localhost:8000
```

#### Example Response (JSON)
```json
{
  "candidate_id": "cand_peel_001_seq01",
  "scenario_id": "peel_001",
  "predicted_pattern_type": "peeling_chain",
  "confidence": 0.942,
  "typology_heuristic_match": {
    "heuristic_name": "peeling_chain_traversal",
    "chain_length": 5,
    "average_peeled_amount_btc": 0.05260000,
    "change_address_reuse_count": 4,
    "reconvergence_detected": false
  },
  "ml_feature_attributions": [
    {
      "feature_name": "propagation_delta_ms",
      "value": 188.0,
      "shap_value": 0.312,
      "direction": "RISK_INCREASING"
    },
    {
      "feature_name": "num_outputs",
      "value": 2,
      "shap_value": 0.285,
      "direction": "RISK_INCREASING"
    },
    {
      "feature_name": "node_type_bulletproof_host",
      "value": 1,
      "shap_value": 0.210,
      "direction": "RISK_INCREASING"
    },
    {
      "feature_name": "fee_ratio",
      "value": 0.00133179,
      "shap_value": -0.045,
      "direction": "RISK_DECREASING"
    }
  ],
  "telemetry_summary": {
    "origin_ips": [
      "38.148.127.142",
      "185.220.101.5"
    ],
    "origin_asns": [
      "AS55836",
      "AS210644"
    ],
    "countries": [
      "IN",
      "DE"
    ],
    "infrastructure_distribution": {
      "residential": 1,
      "bulletproof_host": 4
    }
  },
  "transactions": [
    {
      "txid": 58234917,
      "timestamp": "2014-03-15 09:22:41",
      "input_addresses": ["12dhqUGwzF6c6eW5F7DkyXyqBmW1"],
      "output_addresses": [
        "1EcgU6KKSdjtWmXzy5W3EX34ibCoH",
        "1PZDhrao8CqYBnFzEk67TbPxX8MxbKjhmh"
      ],
      "input_amounts": [0.26361416],
      "output_amounts": [0.05260000, 0.21066308],
      "fee_btc": 0.00035108,
      "script_type": "P2PKH",
      "relay_ip": "38.148.127.142",
      "node_type": "residential",
      "country_code": "IN",
      "asn": "AS55836"
    }
  ]
}
```
