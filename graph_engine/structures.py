"""
graph_engine/structures.py — Shared data-structure definitions.

The ``CandidateStructure`` dataclass is the common output type for every
typology detector. It is imported by the detectors, features.py, export.py,
and validate.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CandidateStructure:
    """
    Represents one detected laundering-typology candidate structure.

    Attributes
    ----------
    candidate_id : str
        Unique identifier, e.g. ``"peel_0001"``, ``"layer_0003"``, ``"mix_0012"``.
    candidate_type : str
        One of ``"peeling_chain"``, ``"layering"``, ``"mixing"``.
    member_txids : list[int]
        All transaction IDs (raw int) whose nodes participate in this structure.
    member_wallets : list[str]
        All wallet address strings (without the ``w:`` prefix) in the structure.
    member_ips : list[str]
        All relay IP strings (without the ``ip:`` prefix) involved.
        Populated by ``features.py`` after detection.
    features : dict
        Feature vector as key→value pairs. Keys are typology-specific.
        Populated by ``features.py``.
    hop_sequence : list[dict] | None
        Ordered hop descriptors for chain-based structures (peeling, layering).
        ``None`` for cluster-based structures (mixing).
    """

    candidate_id:   str
    candidate_type: str
    member_txids:   list[int]         = field(default_factory=list)
    member_wallets: list[str]         = field(default_factory=list)
    member_ips:     list[str]         = field(default_factory=list)
    features:       dict              = field(default_factory=dict)
    hop_sequence:   list[dict] | None = None
