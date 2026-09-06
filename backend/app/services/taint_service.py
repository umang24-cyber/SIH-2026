"""
Seed-Based Risk Propagation & Taint Analysis Engine.
Tracks downstream dirty coin propagation (Haircut & FIFO taint models) from seed illicit addresses.
Runs 100% offline in-memory without external dependencies.
"""
import logging
from typing import Dict, List, Set
from collections import deque
from backend.app.services.data_service import data_service
from backend.app.models.schemas import TaintResponse, TaintNode

logger = logging.getLogger(__name__)

class TaintService:
    def propagate_taint(
        self,
        seed_address: str,
        decay_rate: float = 0.85,
        max_depth: int = 5,
        min_taint_threshold: float = 0.01
    ) -> TaintResponse:
        """
        Calculates forward risk / taint scores from a flagged seed address across outgoing UTXOs.
        Taint score decays per hop according to distance decay and proportional output split.
        """
        if seed_address not in data_service.unique_wallets:
            return TaintResponse(
                seed_address=seed_address,
                decay_rate=decay_rate,
                max_depth=max_depth,
                total_tainted_wallets=0,
                total_tainted_volume_btc=0.0,
                contaminated_wallets=[]
            )

        # BFS Queue holds: (current_address, current_taint_score, current_hop, via_txid)
        queue = deque([(seed_address, 1.0, 0, 0)])
        visited_hops: Dict[str, int] = {seed_address: 0}
        contaminated: Dict[str, TaintNode] = {}
        total_tainted_vol = 0.0

        while queue:
            curr_addr, curr_taint, hop, via_tx = queue.popleft()

            if hop >= max_depth or curr_taint < min_taint_threshold:
                continue

            # Outgoing transactions where curr_addr is an input
            outgoing_txids = data_service.address_in_map.get(curr_addr, [])
            for txid in outgoing_txids:
                tx = data_service.txid_map.get(txid)
                if not tx:
                    continue

                total_in_btc = sum(tx.get("input_amounts", [1.0]))
                out_addresses = tx.get("output_addresses", [])
                out_amounts = tx.get("output_amounts", [])
                total_out_btc = sum(out_amounts)

                # Proportion of input contributed by curr_addr
                curr_contrib_btc = sum(
                    amt for in_a, amt in zip(tx["input_addresses"], tx["input_amounts"]) if in_a == curr_addr
                )
                input_fraction = curr_contrib_btc / max(0.00000001, total_in_btc)

                for out_addr, out_amt in zip(out_addresses, out_amounts):
                    if out_addr == curr_addr:
                        continue  # Skip direct self-loops in queue

                    # Output proportion (Haircut model)
                    output_fraction = out_amt / max(0.00000001, total_out_btc)
                    new_taint = round(curr_taint * input_fraction * output_fraction * decay_rate, 4)

                    if new_taint >= min_taint_threshold:
                        # Check if exchange
                        is_exc = len(data_service.address_out_map.get(out_addr, [])) >= 50
                        
                        if out_addr not in contaminated or new_taint > contaminated[out_addr].taint_score:
                            node = TaintNode(
                                address=out_addr,
                                hop_distance=hop + 1,
                                taint_score=new_taint,
                                received_btc_from_seed=round(out_amt * input_fraction, 8),
                                via_txid=txid,
                                is_licit_exchange=is_exc
                            )
                            contaminated[out_addr] = node
                            total_tainted_vol += out_amt * input_fraction

                        if out_addr not in visited_hops or hop + 1 < visited_hops[out_addr]:
                            visited_hops[out_addr] = hop + 1
                            queue.append((out_addr, new_taint, hop + 1, txid))

        # Sort contaminated wallets by taint score descending
        sorted_nodes = sorted(contaminated.values(), key=lambda n: n.taint_score, reverse=True)

        return TaintResponse(
            seed_address=seed_address,
            decay_rate=decay_rate,
            max_depth=max_depth,
            total_tainted_wallets=len(sorted_nodes),
            total_tainted_volume_btc=round(total_tainted_vol, 8),
            contaminated_wallets=sorted_nodes[:100]
        )

# Global Singleton Instance
taint_service = TaintService()
