"""
detectors/dedup.py — Deduplication and maximal structure merging.

Provides cross-candidate deduplication utilities to ensure that smaller
sub-structures are pruned in favor of longer, maximal candidate structures
without discarding distinct analytical perspectives across typologies.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from graph_engine.structures import CandidateStructure

log = logging.getLogger(__name__)


def merge_maximal_chains(candidates: list[CandidateStructure]) -> list[CandidateStructure]:
    """
    Remove candidates whose member txid sets are strict subsets of another candidate.
    For identical txid sets, retains the first encountered candidate.

    Parameters
    ----------
    candidates : list[CandidateStructure]
        Input list of candidate structures (typically of the same candidate_type).

    Returns
    -------
    list[CandidateStructure]
        Filtered list of maximal candidates.
    """
    if not candidates:
        return []

    sets = [frozenset(c.member_txids) for c in candidates]
    keep: list[CandidateStructure] = []

    for i, cand in enumerate(candidates):
        cand_set = sets[i]

        # Check if strictly dominated by any other candidate
        dominated = any(
            cand_set < sets[j]
            for j in range(len(candidates))
            if j != i
        )
        if dominated:
            continue

        # Check if identical to an earlier candidate already processed
        duplicate = any(
            cand_set == sets[j]
            for j in range(i)
        )
        if duplicate:
            continue

        keep.append(cand)

    log.debug("merge_maximal_chains: %d input -> %d output", len(candidates), len(keep))
    return keep


def merge_all(candidates: list[CandidateStructure]) -> list[CandidateStructure]:
    """
    Group candidates by `candidate_type`, apply maximal set deduplication within
    each group separately, and recombine the results.

    Parameters
    ----------
    candidates : list[CandidateStructure]
        Combined list of candidate structures across various typologies.

    Returns
    -------
    list[CandidateStructure]
        Deduplicated candidates list.
    """
    if not candidates:
        return []

    grouped: dict[str, list[CandidateStructure]] = defaultdict(list)
    for c in candidates:
        grouped[c.candidate_type].append(c)

    result: list[CandidateStructure] = []
    for c_type, group in grouped.items():
        deduped = merge_maximal_chains(group)
        result.extend(deduped)

    log.info("merge_all: %d input -> %d output across %d typologies",
             len(candidates), len(result), len(grouped))
    return result
