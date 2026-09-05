/**
 * graphLoader.worker.ts
 * ─────────────────────
 * Web Worker: fetches a scenario from the live graph API, computes deterministic
 * 3D positions (cluster-sphere packing), builds typed Float32Arrays, and sends
 * them back via zero-copy postMessage transferables.
 *
 * The main thread receives:
 *   { type: 'PROGRESS', pct: number, message: string }
 *   { type: 'DONE', payload: GraphPayload }   ← with transferable buffers
 *   { type: 'ERROR', message: string }
 */

export interface NodeRecord {
  id: string;
  node_type: 'wallet' | 'transaction' | 'ip';
  candidate_ids: string[];
  /** Optional extra fields used for hover-card display */
  address?: string;
  txid?: number;
  relay_ip?: string;
  asn?: string;
  isp?: string;
  degree_in?: number;
  degree_out?: number;
  timestamp?: string;
  fee_btc?: number;
  total_input_btc?: number;
  total_output_btc?: number;
}

export interface EdgeRecord {
  source: string;
  target: string;
  edge_type: string;
  amount_btc?: number;
  candidate_ids: string[];
}

export interface CandidateRecord {
  candidate_id: string;
  candidate_type: 'peeling_chain' | 'layering' | 'mixing';
  member_txids: number[];
  member_wallets: string[];
  member_ips: string[];
  features: Record<string, number>;
  hop_sequence?: Array<{
    hop: number;
    from_wallet: string;
    to_wallet: string;
    txid: number;
    amount_btc: number;
    peeled_btc?: number;
    timestamp: string;
  }>;
}

export interface GraphPayload {
  /** Flat Float32Array: [x0,y0,z0, x1,y1,z1, ...] length = nodeCount*3 */
  positions: Float32Array;
  /**
   * Flat Uint8Array: [r0,g0,b0, r1,g1,b1, ...] 0-255
   * Colour legend:
   *   wallet benign   → dim green (0,80,20)
   *   wallet suspect  → red       (200,20,20)
   *   transaction     → slate     (40,80,120)
   *   ip-node         → gold      (150,120,0)
   */
  colors: Uint8Array;
  /**
   * Flat Float32Array for the sampled edge LineSegments:
   * [x0s,y0s,z0s, x0t,y0t,z0t,  x1s, ...] length = edgeSampleCount*6
   */
  edgePositions: Float32Array;
  /** Parallel to positions: node ID strings (for raycasting lookup) */
  nodeIds: string[];
  /** Parallel to positions: candidate_ids per node (may be empty) */
  nodeCandidateIds: string[][];
  /** Node type per node */
  nodeTypes: Uint8Array; // 0=wallet, 1=transaction, 2=ip
  /** Original candidate objects (for detail-on-demand panel) */
  candidates: CandidateRecord[];
  /** Total counts */
  nodeCount: number;
  edgeCount: number;
  candidateCount: number;
}

// ─── Deterministic 3D position formula ───────────────────────────────────────
// Uses the node's index (i) + node_type + candidate affiliation to place nodes
// in a visually clustered sphere arrangement.
//
// Cluster centres (AML typology separation):
//   Benign wallets  →  [0, 0, 0]        (central dense core)
//   Peeling chain   → [-180, 40, 0]     (left wing)
//   Layering        → [180, 40, -30]    (right wing)
//   Mixing          → [0, -160, 60]     (lower lobe)
//   Transactions    → sparse shell around their owning wallet
//   IP nodes        → outermost shell

const CLUSTER_CENTRES: Record<string, [number, number, number]> = {
  peeling_chain: [-180, 40, 0],
  layering:       [180, 40, -30],
  mixing:         [0, -160, 60],
  benign:         [0, 0, 0],
};

// Deterministic pseudo-random based on string hash (no Math.random)
function hashStr(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = (Math.imul(31, h) + s.charCodeAt(i)) | 0;
  }
  return h;
}

function deterministicPos(
  nodeId: string,
  idx: number,
  nodeType: string,
  primaryCandType: string | null
): [number, number, number] {
  const centre = CLUSTER_CENTRES[primaryCandType ?? 'benign'] ?? [0, 0, 0];

  // Cluster radius varies by type
  const baseRadius =
    nodeType === 'wallet'      ? 80 :
    nodeType === 'transaction' ? 110 :
    /* ip */                     140;

  // Fibonacci sphere point (deterministic, good angular distribution)
  // Use idx + hash to break any accidental symmetry
  const h = Math.abs(hashStr(nodeId));
  const n = 460000; // approximate total
  const goldenAngle = Math.PI * (3 - Math.sqrt(5)); // ~2.399 rad
  const fi = idx / n; // 0..1
  const theta = goldenAngle * (idx + (h % 1000));
  const cosLat = 1 - 2 * fi;
  const sinLat = Math.sqrt(1 - cosLat * cosLat);

  // Slightly randomise radius using hash so nodes don't sit on a perfect shell
  const r = baseRadius * (0.6 + (h % 100) / 250);

  const x = centre[0] + r * sinLat * Math.cos(theta);
  const y = centre[1] + r * cosLat;
  const z = centre[2] + r * sinLat * Math.sin(theta);

  return [x, y, z];
}

function normaliseApiNode(node: any): NodeRecord {
  const type = String(node.type || '').toLowerCase();
  const properties = node.properties || {};
  if (type === 'transaction') {
    const txid = properties.txid ?? String(node.id).replace(/^tx_/, '');
    return {
      id: `tx:${txid}`,
      node_type: 'transaction',
      candidate_ids: [],
      txid: Number(txid),
      timestamp: properties.timestamp,
      fee_btc: Number(properties.fee_btc ?? 0),
      total_input_btc: Number(properties.total_input_btc ?? 0),
      total_output_btc: Number(properties.total_output_btc ?? 0),
    };
  }
  if (type === 'ip') {
    const ip = String(properties.relay_ip ?? String(node.id).replace(/^ip_/, ''));
    return { id: `ip:${ip}`, node_type: 'ip', candidate_ids: [], relay_ip: ip, asn: properties.asn, isp: properties.isp };
  }
  const address = String(properties.address ?? node.id);
  return { id: `w:${address}`, node_type: 'wallet', candidate_ids: [], address };
}

// ─── Worker entry point ───────────────────────────────────────────────────────
self.onmessage = async (event: MessageEvent) => {
  try {
    const scenarioId = event.data?.scenarioId as string | undefined;
    if (!scenarioId) throw new Error('A scenario ID is required for the live graph view');

    // 1. Fetch a scenario graph from the live FastAPI backend.
    postMessage({ type: 'PROGRESS', pct: 2, message: `Fetching live graph: ${scenarioId} …` });

    const resp = await fetch(`/graph/${encodeURIComponent(scenarioId)}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);

    postMessage({ type: 'PROGRESS', pct: 20, message: 'Deserialising live graph structure …' });
    const apiData = await resp.json() as {
      nodes: Array<{ id: string; type: string; properties?: Record<string, any> }>;
      edges: Array<{ source: string; target: string; type: string; properties?: Record<string, any> }>;
    };
    const rawNodes = apiData.nodes || [];
    const rawEdges = apiData.edges || [];
    const nodeIdMap = new Map<string, string>();
    const nodes = rawNodes.map(node => {
      const normalised = normaliseApiNode(node);
      nodeIdMap.set(node.id, normalised.id);
      return normalised;
    });
    const edges: EdgeRecord[] = rawEdges.map(edge => ({
      source: nodeIdMap.get(edge.source) ?? edge.source,
      target: nodeIdMap.get(edge.target) ?? edge.target,
      edge_type: edge.type,
      amount_btc: Number(edge.properties?.amount_btc ?? 0),
      candidate_ids: [],
    }));
    const candidates: CandidateRecord[] = [];

    postMessage({ type: 'PROGRESS', pct: 50, message: `Building position buffers (${nodes.length.toLocaleString()} nodes) …` });

    // 2. Build a map: nodeId → primary candidate type
    const nodeToCandType = new Map<string, string>();
    for (const cand of candidates) {
      const ct = cand.candidate_type;
      for (const w of cand.member_wallets) {
        if (!nodeToCandType.has(`w:${w}`)) nodeToCandType.set(`w:${w}`, ct);
      }
      for (const txid of cand.member_txids) {
        if (!nodeToCandType.has(`tx:${txid}`)) nodeToCandType.set(`tx:${txid}`, ct);
      }
      for (const ip of cand.member_ips) {
        if (!nodeToCandType.has(`ip:${ip}`)) nodeToCandType.set(`ip:${ip}`, ct);
      }
    }

    // 3. Allocate typed arrays
    const nodeCount = nodes.length;
    const positions   = new Float32Array(nodeCount * 3);
    const colors      = new Uint8Array(nodeCount * 3);
    const nodeTypesArr = new Uint8Array(nodeCount); // 0=wallet, 1=tx, 2=ip
    const nodeIds: string[] = new Array(nodeCount);
    const nodeCandidateIds: string[][] = new Array(nodeCount);

    // Position index map: nodeId → buffer index (for edge lookup)
    const nodeIndex = new Map<string, number>();

    for (let i = 0; i < nodeCount; i++) {
      const n = nodes[i];
      const candType = nodeToCandType.get(n.id) ?? null;
      const [x, y, z] = deterministicPos(n.id, i, n.node_type, candType);

      positions[i * 3]     = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;

      // Color encoding
      if (n.node_type === 'wallet') {
        nodeTypesArr[i] = 0;
        if (candType === 'peeling_chain') {
          colors[i * 3] = 220; colors[i * 3 + 1] = 40; colors[i * 3 + 2] = 20; // Red
        } else if (candType === 'layering') {
          colors[i * 3] = 240; colors[i * 3 + 1] = 140; colors[i * 3 + 2] = 0; // Amber
        } else if (candType === 'mixing') {
          colors[i * 3] = 60;  colors[i * 3 + 1] = 120; colors[i * 3 + 2] = 255; // Blue
        } else {
          colors[i * 3] = 0;   colors[i * 3 + 1] = 90;  colors[i * 3 + 2] = 30;  // Green
        }
      } else if (n.node_type === 'transaction') {
        nodeTypesArr[i] = 1;
        colors[i * 3] = 30; colors[i * 3 + 1] = 80; colors[i * 3 + 2] = 130; // Slate
      } else {
        nodeTypesArr[i] = 2;
        colors[i * 3] = 160; colors[i * 3 + 1] = 120; colors[i * 3 + 2] = 0; // Gold
      }

      nodeIds[i] = n.id;
      nodeCandidateIds[i] = n.candidate_ids ?? [];
      nodeIndex.set(n.id, i);

      if (i % 50000 === 0) {
        postMessage({
          type: 'PROGRESS',
          pct: 50 + Math.round((i / nodeCount) * 30),
          message: `Layout: ${i.toLocaleString()} / ${nodeCount.toLocaleString()} nodes …`
        });
      }
    }

    postMessage({ type: 'PROGRESS', pct: 80, message: 'Building edge buffers (sampled subset) …' });

    // 4. Edge buffer — sample max 80,000 edges to keep GPU memory reasonable
    const MAX_EDGES = 80_000;
    const edgeSample = edges.length > MAX_EDGES
      ? edges.filter((_, i) => i % Math.ceil(edges.length / MAX_EDGES) === 0)
      : edges;

    const edgePositions = new Float32Array(edgeSample.length * 6);
    let eidx = 0;
    for (const e of edgeSample) {
      const si = nodeIndex.get(e.source);
      const ti = nodeIndex.get(e.target);
      if (si === undefined || ti === undefined) continue;

      edgePositions[eidx++] = positions[si * 3];
      edgePositions[eidx++] = positions[si * 3 + 1];
      edgePositions[eidx++] = positions[si * 3 + 2];
      edgePositions[eidx++] = positions[ti * 3];
      edgePositions[eidx++] = positions[ti * 3 + 1];
      edgePositions[eidx++] = positions[ti * 3 + 2];
    }
    const edgePosActual = edgePositions.slice(0, eidx);

    postMessage({ type: 'PROGRESS', pct: 95, message: 'Transferring buffers to main thread …' });

    const payload: GraphPayload = {
      positions,
      colors,
      edgePositions: edgePosActual,
      nodeIds,
      nodeCandidateIds,
      nodeTypes: nodeTypesArr,
      candidates,
      nodeCount,
      edgeCount: edges.length,
      candidateCount: candidates.length,
    };

    // Zero-copy transfer
    (self as any).postMessage(
      { type: 'DONE', payload },
      [positions.buffer, colors.buffer, edgePosActual.buffer, nodeTypesArr.buffer]
    );
  } catch (err: any) {
    postMessage({ type: 'ERROR', message: err?.message ?? String(err) });
  }
};
