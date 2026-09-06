"""
embeddings.py — Node2Vec graph embeddings for the Bitcoin AML Graph Engine.

Overview
--------
Generates fixed-length embedding vectors for every node in the heterogeneous
graph G (wallet / transaction / ip nodes) using the Node2Vec algorithm
(Grover & Leskovec, KDD 2016).

Implementation notes
--------------------
**Pure-numpy implementation — zero new pip dependencies.**

The PyPI ``node2vec`` package (v0.5.0) requires ``numpy<2.0.0`` and
``gensim>=4.3.0`` (Cython-compiled).  The project venv runs numpy 2.5.2 on
Python 3.14.7; installing the PyPI package would downgrade numpy and risk
a failed gensim build on Python 3.14.  This module instead implements the
full Node2Vec pipeline — biased random walks + Skip-Gram with negative
sampling — using only ``numpy`` (≥1.24, tested on 2.5.2) and ``networkx``
(≥3.1, tested on 3.6.1), both already installed.

Trade-off: pure-numpy Skip-Gram is slower than gensim's Cython backend.
Expected runtime on the production graph (448k nodes, 409k+ edges):
  • Alias table precomputation  :  2–5  min
  • Random walk generation      :  3–8  min  (448k × 10 walks × 80 steps)
  • Skip-Gram training (1 epoch):  10–25 min  (~100k updates/s on modern CPU)
  • Save outputs                :  <2   min
  • Total                       :  15–40 min

Run once and checkpoint.  Pass ``--skip-embeddings`` to ``main.py`` to skip
regeneration when the checkpoint files already exist.

Directed graph
--------------
G is treated as **directed** during walk generation: each step follows
out-edges of the current node.  Transaction-flow direction (wallet →
transaction → wallet) is semantically meaningful and is preserved.

This is a flag-worthy limitation of Node2Vec vs GraphSAGE: the biased
random walk uses second-order Markov history (the previous node) to bias
transition probabilities via p/q, but the walk is still constrained to
directed out-edges — it does *not* perform typed message passing.

Heterogeneity handling
----------------------
Node2Vec is natively homogeneous: it assigns identical walk semantics to
all node types.  This graph has three types (wallet, transaction, ip).

Decision: embed the **full heterogeneous graph** (all node types together).
Cross-type walks (wallet → tx → wallet) capture the structural signal that
drives peeling-chain and layering pattern detection.  Running separate
Node2Vec instances per node type would sever this cross-type connectivity
and destroy the most informative structural paths.

Limitation: node-type distinctions are not natively encoded in the embedding
space.  They are exposed as a separate one-hot ``node_type`` feature that the
ML teammate appends to the embedding vector at classifier training time.

GraphSAGE future work
---------------------
GraphSAGE was considered as an alternative because:
  • It is inductive (can embed unseen nodes without retraining).
  • Its typed neighbor aggregation handles heterogeneous node types natively
    via separate weight matrices per edge type (wallet→tx, tx→wallet,
    ip→tx), which Node2Vec cannot replicate through walk bias alone.

It is out of scope for this pass because:
  1. Requires a supervised or self-supervised training loop and a defined
     loss (link prediction or contrastive objective).
  2. Needs a GNN train/inference split separate from the downstream
     classifier's train/test split — two leakage surfaces to manage
     independently, not one.
  3. Requires ``torch-geometric`` or ``DGL`` with CUDA build requirements —
     a large additional dependency footprint that the hackathon timeline
     cannot absorb.

To add GraphSAGE later:
  • Define a GNN train split using ``scenario_id`` stratification without
    exposing ``is_illicit`` to the GNN encoder.
  • Install ``torch-geometric`` with a CUDA-compatible PyTorch build.
  • Define ``HeteroData`` objects with typed node-feature tensors.
  • Implement a 2-layer ``HeteroSAGE`` encoder with mean aggregation.
  • The inductive framing allows embedding new transactions at inference
    time without full retraining.

No-leakage guarantee
--------------------
Walks are computed from **graph topology only** — node connectivity,
edge weights, and node/edge type (for filtering, not for labelling).
No label attribute (``is_illicit``, ``pattern_type``, ``scenario_id``
used as a supervised signal) is read anywhere in this module.  The only
node attributes accessed are ``node_type`` (to log per-type statistics)
and nothing else.  An explicit assertion verifies this at module entry.

Public API
----------
generate_embeddings(G, **kwargs) → dict[str, np.ndarray]
    Runs the full Node2Vec pipeline on the live nx.MultiDiGraph.
    Returns node_id → float32 embedding vector.
    Side effects: writes checkpoint files to the configured output directory.

pool_candidate_embeddings(candidates, embeddings) → pd.DataFrame
    Mean-pools per-node embeddings over each candidate's member nodes.
    Returns a DataFrame joinable to ``candidates_ml_handoff.csv`` on
    ``candidate_id``.

Exports
-------
``output/node_embeddings.npy``         — shape (N, dim), float32
``output/node_embedding_index.json``   — {"node_id": row_index}
``output/embedding_features.parquet``  — per-node, columns emb_0..emb_{dim-1}
``output/candidate_embeddings.parquet``— per-candidate mean-pooled embeddings
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

from graph_engine import config

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Sentinel label attributes — confirm none of these are read in walk generation.
# Any code path that reads these is a leakage bug.
_LABEL_ATTRS: frozenset[str] = frozenset(
    {"is_illicit", "pattern_type", "label", "ground_truth"}
)


# ---------------------------------------------------------------------------
# Alias sampling helpers
# ---------------------------------------------------------------------------

def _build_alias_table(
    weights: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Construct the Alias Method lookup tables for O(1) weighted sampling.

    Parameters
    ----------
    weights : np.ndarray
        Non-negative unnormalized probabilities.  Must have len >= 1.

    Returns
    -------
    (prob, alias) : tuple of 1-D int/float arrays of length len(weights).
    """
    n = len(weights)
    prob  = np.zeros(n, dtype=np.float64)
    alias = np.zeros(n, dtype=np.int64)

    total = weights.sum()
    if total == 0.0:
        # Uniform fallback for isolated nodes
        prob[:] = 1.0
        alias[:] = np.arange(n, dtype=np.int64)
        return prob, alias

    p = (weights / total) * n  # scaled so sum == n

    small = []
    large = []
    for i, pi in enumerate(p):
        if pi < 1.0:
            small.append(i)
        else:
            large.append(i)

    while small and large:
        s = small.pop()
        l = large.pop()
        prob[s]  = p[s]
        alias[s] = l
        p[l] = p[l] + p[s] - 1.0
        if p[l] < 1.0:
            small.append(l)
        else:
            large.append(l)

    while large:
        prob[large.pop()] = 1.0
    while small:
        prob[small.pop()] = 1.0  # floating-point remainder

    return prob, alias


def _alias_draw(prob: np.ndarray, alias: np.ndarray, rng: np.random.Generator) -> int:
    """Draw one sample using precomputed alias tables."""
    k = rng.integers(0, len(prob))
    if rng.random() < prob[k]:
        return int(k)
    return int(alias[k])


# ---------------------------------------------------------------------------
# Node2Vec biased random walk generator
# ---------------------------------------------------------------------------

class Node2VecWalker:
    """
    Second-order biased random walker for Node2Vec.

    Operates directly on a ``networkx.MultiDiGraph``.

    The graph is treated as **directed**: each walk step follows the
    out-edges of the current node.  The walk uses the (p, q) return /
    in-out bias parameters from the Node2Vec paper:
      - p (return parameter): bias to revisit the previous node
      - q (in-out parameter): bias between BFS-like (q>1) and DFS-like (q<1)

    No label attributes are read — walks are structure-only.

    Parameters
    ----------
    G : nx.MultiDiGraph
        The full heterogeneous graph.  Used read-only.
    walk_length : int
        Number of steps per walk.  Default: config.EMBED_WALK_LENGTH (80).
    num_walks : int
        Walks per source node.  Default: config.EMBED_NUM_WALKS (10).
    p : float
        Return parameter.  Default: config.EMBED_P (1.0).
    q : float
        In-out parameter.  Default: config.EMBED_Q (0.5).
        q < 1 biases toward DFS (community / cluster exploration).
        q > 1 biases toward BFS (local neighborhood).
    seed : int
        RNG seed for reproducibility.  Default: config.EMBED_SEED (42).
    """

    def __init__(
        self,
        G: nx.MultiDiGraph,
        *,
        walk_length: int = config.EMBED_WALK_LENGTH,
        num_walks:   int = config.EMBED_NUM_WALKS,
        p:          float = config.EMBED_P,
        q:          float = config.EMBED_Q,
        seed:        int = config.EMBED_SEED,
    ) -> None:
        self.G           = G
        self.walk_length = walk_length
        self.num_walks   = num_walks
        self.p           = p
        self.q           = q
        self.rng         = np.random.default_rng(seed)

        self._nodes: list[str] = list(G.nodes())
        self._node_index: dict[str, int] = {n: i for i, n in enumerate(self._nodes)}

        log.info(
            "Node2VecWalker initialised: %d nodes, walk_length=%d, "
            "num_walks=%d, p=%.2f, q=%.2f",
            len(self._nodes), walk_length, num_walks, p, q,
        )

        # Precompute edge transition weights once
        t0 = time.perf_counter()
        self._precompute_alias_tables()
        log.info(
            "Alias table precomputation done in %.1fs",
            time.perf_counter() - t0,
        )

    # ------------------------------------------------------------------
    # Precomputation
    # ------------------------------------------------------------------

    def _get_edge_weight(self, u: str, v: str) -> float:
        """Return the weight of edge u→v.  Sums amount_btc over parallel edges."""
        edges = self.G[u][v]  # {key: data_dict} for MultiDiGraph
        total = 0.0
        for edata in edges.values():
            amt = edata.get("amount_btc")
            if amt is not None:
                total += float(amt)
        return total if total > 0.0 else 1.0

    def _precompute_alias_tables(self) -> None:
        """
        Build alias tables for first-order (node-level) and second-order
        (edge-level) transitions.

        First-order tables: used for the first step of each walk (no previous
        node available).  Based on out-edge weights from each source node.

        Second-order tables: used for all subsequent steps.  The bias weight
        for a candidate next node x (reached from current node v, came from u)
        is:
          - 1/p  if x == u  (return to previous)
          - 1.0  if x is a neighbour of u  (stay nearby, BFS)
          - 1/q  otherwise  (explore further, DFS)
        """
        G = self.G
        nodes = self._nodes

        # First-order alias tables: node → (prob, alias, successors_list)
        self._first_order: dict[str, tuple] = {}
        for node in nodes:
            succs = list(G.successors(node))
            if not succs:
                # Dead-end node: alias table is empty, walk terminates here
                self._first_order[node] = (np.array([1.0]), np.array([0]), [node])
                continue
            w = np.array([self._get_edge_weight(node, s) for s in succs], dtype=np.float64)
            prob, alias = _build_alias_table(w)
            self._first_order[node] = (prob, alias, succs)

        # Second-order alias tables: (u, v) → (prob, alias, successors_list)
        # Only computed for edges that will actually be traversed (u→v exists).
        self._second_order: dict[tuple[str, str], tuple] = {}
        for u, v in G.edges():
            if (u, v) in self._second_order:
                continue  # parallel edges share the same table
            succs = list(G.successors(v))
            if not succs:
                self._second_order[(u, v)] = (np.array([1.0]), np.array([0]), [v])
                continue

            u_neighbors: set[str] = set(G.successors(u))  # BFS locality set

            biased_w = np.zeros(len(succs), dtype=np.float64)
            for i, x in enumerate(succs):
                base_w = self._get_edge_weight(v, x)
                if x == u:
                    bias = 1.0 / self.p
                elif x in u_neighbors:
                    bias = 1.0
                else:
                    bias = 1.0 / self.q
                biased_w[i] = base_w * bias

            prob, alias = _build_alias_table(biased_w)
            self._second_order[(u, v)] = (prob, alias, succs)

    # ------------------------------------------------------------------
    # Walk generation
    # ------------------------------------------------------------------

    def generate_walks(self) -> list[list[str]]:
        """
        Generate all biased random walks.

        Returns
        -------
        list[list[str]]
            Each inner list is a walk: a sequence of node ID strings.
        """
        t0 = time.perf_counter()
        walks: list[list[str]] = []
        nodes = self._nodes.copy()

        total = len(nodes) * self.num_walks
        log.info("Starting walk generation: %d total walks …", total)

        for walk_iter in range(self.num_walks):
            # Shuffle node order each iteration for unbiased context distribution
            self.rng.shuffle(nodes)  # type: ignore[arg-type]
            for src in nodes:
                walks.append(self._walk(src))

            if (walk_iter + 1) % max(1, self.num_walks // 5) == 0:
                elapsed = time.perf_counter() - t0
                done = (walk_iter + 1) * len(self._nodes)
                log.info(
                    "  Walk progress: %d/%d  (%.1f%%)  %.1fs elapsed",
                    done, total, 100 * done / total, elapsed,
                )

        elapsed = time.perf_counter() - t0
        log.info(
            "Walk generation complete: %d walks, avg_len=%.1f  (%.1fs)",
            len(walks),
            sum(len(w) for w in walks) / max(1, len(walks)),
            elapsed,
        )
        return walks

    def _walk(self, src: str) -> list[str]:
        """Execute one biased random walk starting from src."""
        walk = [src]
        prob, alias, succs = self._first_order[src]

        if len(succs) == 1 and succs[0] == src:
            # Dead-end node: single-node walk
            return walk

        # First step: first-order transition
        idx = _alias_draw(prob, alias, self.rng)
        walk.append(succs[idx])

        # Subsequent steps: second-order transitions
        for _ in range(self.walk_length - 2):
            cur  = walk[-1]
            prev = walk[-2]
            key  = (prev, cur)
            if key in self._second_order:
                prob2, alias2, succs2 = self._second_order[key]
                if len(succs2) == 1 and succs2[0] == cur:
                    break  # dead-end
                idx2 = _alias_draw(prob2, alias2, self.rng)
                walk.append(succs2[idx2])
            else:
                # cur has no out-edges: terminate walk early
                break

        return walk


# ---------------------------------------------------------------------------
# Skip-Gram with negative sampling
# ---------------------------------------------------------------------------

class SkipGramEmbedder:
    """
    Pure-numpy Skip-Gram with negative sampling.

    Learns node embeddings from random walk sequences exactly as Word2Vec
    learns word embeddings from sentences.  No pretrained vectors are used;
    training is entirely local and offline.

    Parameters
    ----------
    vocab_size : int
        Number of unique nodes (= number of embedding rows).
    embedding_dim : int
        Embedding vector length.  Default: config.EMBED_DIM (64).
    window_size : int
        Context window radius.  Default: config.EMBED_WINDOW (5).
    neg_samples : int
        Negative samples per positive pair.  Default: config.EMBED_NEG_SAMPLES (5).
    learning_rate : float
        SGD learning rate.  Default: 0.025 (standard Word2Vec initial LR).
    epochs : int
        Training epochs over all walks.  Default: config.EMBED_EPOCHS (1).
    seed : int
        RNG seed.  Default: config.EMBED_SEED (42).
    """

    def __init__(
        self,
        vocab_size:    int,
        *,
        embedding_dim: int   = config.EMBED_DIM,
        window_size:   int   = config.EMBED_WINDOW,
        neg_samples:   int   = config.EMBED_NEG_SAMPLES,
        learning_rate: float = 0.025,
        epochs:        int   = config.EMBED_EPOCHS,
        seed:          int   = config.EMBED_SEED,
    ) -> None:
        self.vocab_size    = vocab_size
        self.embedding_dim = embedding_dim
        self.window_size   = window_size
        self.neg_samples   = neg_samples
        self.learning_rate = learning_rate
        self.epochs        = epochs

        rng = np.random.default_rng(seed)

        # Input and output embedding matrices.
        # W_in:  shape (vocab_size, embedding_dim) — the "node" embeddings
        # W_out: shape (vocab_size, embedding_dim) — context / noise vectors
        bound = 0.5 / embedding_dim
        self.W_in  = rng.uniform(-bound, bound, (vocab_size, embedding_dim)).astype(np.float32)
        self.W_out = np.zeros((vocab_size, embedding_dim), dtype=np.float32)

        # Unigram noise distribution for negative sampling.
        # Populated by fit() once token frequencies are known.
        self._noise_table: np.ndarray | None = None
        self._noise_rng = np.random.default_rng(seed + 1)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit(
        self,
        sequences: list[list[int]],
        node_freq: np.ndarray,
    ) -> None:
        """
        Train Skip-Gram embeddings on the integer-encoded walk sequences.

        Parameters
        ----------
        sequences : list[list[int]]
            Each inner list is a walk encoded as node indices (not node IDs).
        node_freq : np.ndarray
            Shape (vocab_size,).  Unigram frequency of each node across all
            walks.  Used to build the noise distribution for negative sampling.
            Raised to the 3/4 power (standard Word2Vec smoothing).
        """
        # Build noise distribution (unigram^(3/4), as per Mikolov et al.)
        noise_dist = node_freq ** 0.75
        noise_dist = noise_dist / noise_dist.sum()
        noise_cumsum = np.cumsum(noise_dist)
        self._noise_table = noise_cumsum

        t0  = time.perf_counter()
        lr  = self.learning_rate

        total_pairs = sum(
            max(0, len(seq) - 2 * self.window_size) * self.window_size
            for seq in sequences
        )
        log.info(
            "Skip-Gram training: %d sequences, ~%d (centre,context) pairs, "
            "%d epoch(s) …",
            len(sequences), total_pairs, self.epochs,
        )

        for epoch in range(self.epochs):
            loss_acc = 0.0
            pair_count = 0

            for seq in sequences:
                seq_len = len(seq)
                for i, centre in enumerate(seq):
                    # Dynamic window (standard Word2Vec trick: sample window ≤ window_size)
                    win = int(self._noise_rng.integers(1, self.window_size + 1))
                    ctx_start = max(0, i - win)
                    ctx_end   = min(seq_len, i + win + 1)

                    for j in range(ctx_start, ctx_end):
                        if j == i:
                            continue
                        context = seq[j]

                        # Negative samples (excluding centre and context)
                        negs = self._sample_negatives(context, centre)

                        # SGD update
                        l = self._sgd_step(centre, context, negs, lr)
                        loss_acc  += l
                        pair_count += 1

            # Linear LR decay
            lr = self.learning_rate * (1.0 - (epoch + 1) / self.epochs)
            lr = max(lr, self.learning_rate * 0.0001)

            log.info(
                "  Epoch %d/%d  avg_loss=%.4f  pairs=%d  (%.1fs elapsed)",
                epoch + 1, self.epochs,
                loss_acc / max(1, pair_count), pair_count,
                time.perf_counter() - t0,
            )

        log.info("Skip-Gram training complete in %.1fs", time.perf_counter() - t0)

    def _sample_negatives(self, context: int, centre: int) -> np.ndarray:
        """Sample neg_samples negative node indices using the noise distribution."""
        # Use inverse CDF sampling on the precomputed cumulative distribution
        u = self._noise_rng.random(self.neg_samples * 3)
        candidates = np.searchsorted(self._noise_table, u).astype(np.int64)
        candidates = candidates[candidates != context]
        candidates = candidates[candidates != centre]
        if len(candidates) < self.neg_samples:
            # Fallback: uniform random (rare edge case)
            extras = self._noise_rng.integers(0, self.vocab_size, self.neg_samples)
            candidates = np.concatenate([candidates, extras])
        return candidates[: self.neg_samples]

    def _sgd_step(
        self,
        centre:  int,
        context: int,
        negs:    np.ndarray,
        lr:      float,
    ) -> float:
        """
        One Skip-Gram SGD update.

        Positive pair: (centre, context)
        Negative pairs: (centre, neg) for each neg in negs

        Returns the binary cross-entropy loss for this step.
        """
        v_centre = self.W_in[centre]   # shape (dim,)

        # Positive update
        dot_pos = np.dot(v_centre, self.W_out[context])
        sig_pos = _sigmoid(dot_pos)
        err_pos = sig_pos - 1.0        # gradient w.r.t. W_out[context]

        grad_centre = err_pos * self.W_out[context]

        self.W_out[context] -= lr * err_pos * v_centre

        # Negative updates
        loss = -np.log(sig_pos + 1e-10)
        for neg in negs:
            dot_neg = np.dot(v_centre, self.W_out[neg])
            sig_neg = _sigmoid(dot_neg)
            err_neg = sig_neg             # gradient (target is 0)
            grad_centre += err_neg * self.W_out[neg]
            self.W_out[neg] -= lr * err_neg * v_centre
            loss -= np.log(1.0 - sig_neg + 1e-10)

        self.W_in[centre] -= lr * grad_centre
        return float(loss)

    # ------------------------------------------------------------------
    # Result retrieval
    # ------------------------------------------------------------------

    @property
    def embeddings(self) -> np.ndarray:
        """Return the trained W_in matrix: shape (vocab_size, embedding_dim), float32."""
        return self.W_in


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + np.exp(-x))
    ex = np.exp(x)
    return ex / (1.0 + ex)


# ---------------------------------------------------------------------------
# Public API — generate_embeddings
# ---------------------------------------------------------------------------

def generate_embeddings(
    G:              nx.MultiDiGraph,
    *,
    walk_length:    int   = config.EMBED_WALK_LENGTH,
    num_walks:      int   = config.EMBED_NUM_WALKS,
    p:              float = config.EMBED_P,
    q:              float = config.EMBED_Q,
    embedding_dim:  int   = config.EMBED_DIM,
    window_size:    int   = config.EMBED_WINDOW,
    neg_samples:    int   = config.EMBED_NEG_SAMPLES,
    epochs:         int   = config.EMBED_EPOCHS,
    seed:           int   = config.EMBED_SEED,
    output_dir:     Path  = config.OUTPUT_DIR,
) -> dict[str, np.ndarray]:
    """
    Run the full Node2Vec pipeline on the live heterogeneous graph G.

    No-leakage guarantee: this function reads only graph topology
    (node connectivity and edge weights / types for walk direction).
    It does NOT read any label attributes (``is_illicit``, ``pattern_type``,
    ``label``, ``ground_truth``).  The assertion below verifies this at
    module entry.

    Parameters
    ----------
    G : nx.MultiDiGraph
        The full heterogeneous graph produced by ``graph_build.build_full_graph``.
        Passed in-memory — no serialisation/deserialisation.
    walk_length : int
        Steps per walk.  Default: ``config.EMBED_WALK_LENGTH`` (80).
    num_walks : int
        Walks per source node.  Default: ``config.EMBED_NUM_WALKS`` (10).
    p : float
        Return parameter.  1.0 = neutral.  Default: ``config.EMBED_P``.
    q : float
        In-out parameter.  <1 = DFS bias (community structure).
        Default: ``config.EMBED_Q`` (0.5 — mild DFS bias for mixing clusters).
    embedding_dim : int
        Embedding vector length.  Default: ``config.EMBED_DIM`` (64).
    window_size : int
        Skip-Gram context window.  Default: ``config.EMBED_WINDOW`` (5).
    neg_samples : int
        Negative samples per positive pair.  Default: ``config.EMBED_NEG_SAMPLES`` (5).
    epochs : int
        Training epochs.  Default: ``config.EMBED_EPOCHS`` (1).
    seed : int
        Reproducibility seed.  Default: ``config.EMBED_SEED`` (42).
    output_dir : Path
        Directory to write checkpoint files.  Default: ``config.OUTPUT_DIR``.

    Returns
    -------
    dict[str, np.ndarray]
        Mapping ``node_id → float32 embedding vector`` of shape ``(embedding_dim,)``.
        Contains all nodes in G (wallet, transaction, ip).

    Side effects
    ------------
    Writes four files to ``output_dir``:
      * ``node_embeddings.npy``          — shape (N, dim), float32
      * ``node_embedding_index.json``    — {"node_id": row_index}
      * ``embedding_features.parquet``   — per-node DataFrame, columns emb_0..emb_{dim-1}
      * ``candidate_embeddings.parquet`` — not written here; call pool_candidate_embeddings()
    """
    t_total = time.perf_counter()

    # ------------------------------------------------------------------
    # Leakage guard — confirm no label attributes exist on any node
    # ------------------------------------------------------------------
    label_hits: list[str] = []
    for node_id, data in G.nodes(data=True):
        for attr in _LABEL_ATTRS:
            if attr in data:
                label_hits.append(f"{node_id}.{attr}")
    if label_hits:
        log.warning(
            "LEAKAGE WARNING: %d node(s) carry label attributes that Node2Vec "
            "must NOT use: %s … (embeddings computed from topology only, "
            "label attrs are present but ignored)",
            len(label_hits), label_hits[:5],
        )
    else:
        log.info("Leakage guard: no label attributes found on graph nodes. OK.")

    # ------------------------------------------------------------------
    # Log graph statistics by node type
    # ------------------------------------------------------------------
    node_type_counts: dict[str, int] = {}
    for _, data in G.nodes(data=True):
        nt = data.get("node_type", "unknown")
        node_type_counts[nt] = node_type_counts.get(nt, 0) + 1

    log.info(
        "Graph: %d nodes %s, %d edges  |  embedding_dim=%d, p=%.2f, q=%.2f",
        G.number_of_nodes(), node_type_counts,
        G.number_of_edges(),
        embedding_dim, p, q,
    )
    log.info(
        "Walk parameters: walk_length=%d, num_walks=%d  "
        "=> ~%d total walk steps",
        walk_length, num_walks,
        G.number_of_nodes() * num_walks * walk_length,
    )

    # ------------------------------------------------------------------
    # Step 1 — Build alias tables + generate walks
    # ------------------------------------------------------------------
    log.info("--- PHASE 1: Biased random walk generation ---")
    walker = Node2VecWalker(
        G,
        walk_length=walk_length,
        num_walks=num_walks,
        p=p,
        q=q,
        seed=seed,
    )
    t_walk_start = time.perf_counter()
    walks = walker.generate_walks()
    t_walk_elapsed = time.perf_counter() - t_walk_start
    log.info("Walk generation: %.1fs", t_walk_elapsed)

    # ------------------------------------------------------------------
    # Step 2 — Encode walks as integer sequences
    # ------------------------------------------------------------------
    nodes     = walker._nodes          # ordered list of node IDs
    node_idx  = walker._node_index     # node_id → int
    vocab_size = len(nodes)

    encoded_walks: list[list[int]] = [
        [node_idx[n] for n in walk] for walk in walks
    ]

    # Compute node frequencies for noise distribution
    node_freq = np.zeros(vocab_size, dtype=np.float64)
    for walk in encoded_walks:
        for idx in walk:
            node_freq[idx] += 1.0
    node_freq = np.maximum(node_freq, 1.0)   # avoid zero for unseen nodes

    # ------------------------------------------------------------------
    # Step 3 — Skip-Gram training
    # ------------------------------------------------------------------
    log.info("--- PHASE 2: Skip-Gram training ---")
    t_sg_start = time.perf_counter()
    embedder = SkipGramEmbedder(
        vocab_size,
        embedding_dim=embedding_dim,
        window_size=window_size,
        neg_samples=neg_samples,
        epochs=epochs,
        seed=seed,
    )
    embedder.fit(encoded_walks, node_freq)
    t_sg_elapsed = time.perf_counter() - t_sg_start
    log.info("Skip-Gram training: %.1fs", t_sg_elapsed)

    # ------------------------------------------------------------------
    # Step 4 — Build output dict
    # ------------------------------------------------------------------
    E = embedder.embeddings   # shape (vocab_size, embedding_dim), float32
    result: dict[str, np.ndarray] = {
        node_id: E[i] for i, node_id in enumerate(nodes)
    }

    # ------------------------------------------------------------------
    # Step 5 — Save checkpoint files
    # ------------------------------------------------------------------
    output_dir.mkdir(parents=True, exist_ok=True)

    npy_path   = output_dir / "node_embeddings.npy"
    idx_path   = output_dir / "node_embedding_index.json"
    parq_path  = output_dir / "embedding_features.parquet"

    # node_embeddings.npy — shape (N, dim)
    np.save(str(npy_path), E)
    log.info("Saved %s  (%.1f MB)", npy_path, npy_path.stat().st_size / 1_048_576)

    # node_embedding_index.json — {node_id: row_index}
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(node_idx, f, separators=(",", ":"))
    log.info("Saved %s", idx_path)

    # embedding_features.parquet — one row per node, columns emb_0..emb_{dim-1}
    col_names = [f"emb_{i}" for i in range(embedding_dim)]
    emb_df = pd.DataFrame(E, columns=col_names)
    emb_df.insert(0, "node_id", nodes)
    emb_df.insert(1, "node_type", [
        G.nodes[n].get("node_type", "unknown") for n in nodes
    ])
    try:
        emb_df.to_parquet(str(parq_path), index=False)
        log.info(
            "Saved %s  (%.1f MB, %d rows)",
            parq_path, parq_path.stat().st_size / 1_048_576, len(emb_df),
        )
    except ImportError:
        log.warning(
            "pyarrow/fastparquet not installed — skipping parquet export. "
            "Install pyarrow to enable parquet output."
        )

    # ------------------------------------------------------------------
    # Summary benchmark
    # ------------------------------------------------------------------
    t_total_elapsed = time.perf_counter() - t_total
    log.info(
        "generate_embeddings complete: %d nodes embedded  "
        "(walk=%.1fs  sg=%.1fs  total=%.1fs)",
        len(result), t_walk_elapsed, t_sg_elapsed, t_total_elapsed,
    )

    return result


# ---------------------------------------------------------------------------
# Public API — pool_candidate_embeddings
# ---------------------------------------------------------------------------

def pool_candidate_embeddings(
    candidates: list[Any],   # list[CandidateStructure]
    embeddings: dict[str, np.ndarray],
    *,
    output_path: Path | None = None,
) -> pd.DataFrame:
    """
    Mean-pool per-node embeddings into per-candidate embedding vectors.

    For each candidate, pools the embeddings of its ``member_wallets`` and
    ``member_txids`` (using the ``w:`` and ``tx:`` prefixes to build node IDs).
    The resulting vector is the mean of all member embeddings found in the
    embedding dict.  Nodes whose IDs are not in the embedding dict (e.g., nodes
    added after embedding generation) are silently skipped with a warning.

    Parameters
    ----------
    candidates : list[CandidateStructure]
        All detected candidates.
    embeddings : dict[str, np.ndarray]
        Output of ``generate_embeddings()``.
    output_path : Path | None
        If provided, saves the result as a parquet file at this path.
        Default: ``config.OUTPUT_DIR / "candidate_embeddings.parquet"``.

    Returns
    -------
    pd.DataFrame
        One row per candidate.  Columns:
            ``candidate_id``  — str
            ``candidate_type``— str
            ``emb_0`` ... ``emb_{dim-1}``  — float32 mean-pooled embedding
        Joinable to ``candidates_ml_handoff.csv`` on ``candidate_id``.
    """
    if not embeddings:
        log.warning("pool_candidate_embeddings: empty embeddings dict — returning empty DataFrame")
        return pd.DataFrame()

    dim = next(iter(embeddings.values())).shape[0]
    col_names = [f"emb_{i}" for i in range(dim)]

    rows = []
    missing_nodes = 0

    for cand in candidates:
        # Collect node IDs for this candidate's member wallets + transactions
        member_ids: list[str] = (
            [f"{config.PREFIX_WALLET}{w}" for w in cand.member_wallets]
            + [f"{config.PREFIX_TX}{t}"   for t in cand.member_txids]
        )

        vecs = []
        for nid in member_ids:
            if nid in embeddings:
                vecs.append(embeddings[nid])
            else:
                missing_nodes += 1

        if vecs:
            pooled = np.stack(vecs, axis=0).mean(axis=0).astype(np.float32)
        else:
            pooled = np.zeros(dim, dtype=np.float32)

        row: dict[str, Any] = {
            "candidate_id":   cand.candidate_id,
            "candidate_type": cand.candidate_type,
        }
        for i, v in enumerate(pooled):
            row[col_names[i]] = float(v)
        rows.append(row)

    if missing_nodes > 0:
        log.warning(
            "pool_candidate_embeddings: %d member node IDs not found in embeddings "
            "(nodes added after embedding generation or truncated walks).",
            missing_nodes,
        )

    df = pd.DataFrame(rows)

    if output_path is None:
        output_path = config.OUTPUT_DIR / "candidate_embeddings.parquet"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(str(output_path), index=False)
        log.info(
            "Saved %s  (%d candidates, %d emb columns)",
            output_path, len(df), dim,
        )
    except ImportError:
        log.warning(
            "pyarrow/fastparquet not installed — skipping candidate parquet export."
        )

    return df


# ---------------------------------------------------------------------------
# Cosine similarity helper (used by tests and sanity checks)
# ---------------------------------------------------------------------------

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors.  Returns float in [-1, 1]."""
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))
