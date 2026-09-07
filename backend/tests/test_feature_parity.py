import unittest
import pandas as pd
import json
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.data_service import data_service
from backend.app.services.ml_service import ml_service
import importlib

compute_scenario_features = importlib.import_module("ml.02_feature_engineering").compute_scenario_features
compute_graph_features = importlib.import_module("ml.02b_graph_features").compute_graph_features

class TestFeatureParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data_service.initialize()
        ml_service.load_model()

    def test_46_feature_parity(self):
        """Verify that production ML service computes the exact same 46 features as the offline data pipeline."""
        sample_sc = next(iter(data_service.scenario_tx_map.keys()))
        txids = data_service.scenario_tx_map[sample_sc]
        scenario_txs = [data_service.txid_map[tid] for tid in txids]

        # Production inference features
        prod_features = ml_service._feature_dict(scenario_txs)

        # Offline pipeline features
        grp = pd.DataFrame(scenario_txs)
        grp["timestamp"] = pd.to_datetime(grp["timestamp"])
        if "relay_timestamp" in grp.columns:
            grp["relay_timestamp"] = pd.to_datetime(grp["relay_timestamp"])

        for col in ["input_addresses", "output_addresses", "input_amounts", "output_amounts"]:
            if isinstance(grp[col].iloc[0], str):
                grp[col] = grp[col].apply(json.loads)

        base_feats = compute_scenario_features(grp)
        raw_mode = base_feats.pop("_script_type_mode_raw", "P2PKH")
        base_feats["script_type_mode"] = ml_service.script_type_encoder.get(raw_mode, 0)

        graph_feats = compute_graph_features(grp)
        graph_feats.pop("_cycle_detected", None)

        offline_features = {**base_feats, **graph_feats}

        self.assertEqual(len(prod_features), 46, "Production features must strictly equal 46")

        for name in ml_service.feature_names:
            self.assertIn(name, offline_features)
            self.assertAlmostEqual(
                prod_features[name],
                float(offline_features[name]),
                places=4,
                msg=f"Feature {name} mismatch between offline pipeline and production inference"
            )

if __name__ == "__main__":
    unittest.main()
