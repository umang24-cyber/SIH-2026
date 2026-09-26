"""Read-only Observatory. Never uses the mutable case store or evaluates a model.

Artifacts are cached by file size/mtime under a lock. Only aggregate data is
returned; CSV transactions, addresses and investigator uploads are never exposed.
"""
import copy
import csv
import json
import logging
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock

from backend.app.models.observatory import (
    DatasetData, Diagram, FeatureData, ObservatoryMeta, ObservatoryResponse,
    OverviewData, PatternsData, PerformanceData,
)
from backend.app.core.config import DATA_PROCESSED_DIR
from backend.app.services.ml_service import MANIFEST_PATH, BINARY_ILLICIT_THRESHOLD

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[3]
REPORT = "ml/reports/phase5_frozen_test_evaluation_v9.json"
DATA_DIR = DATA_PROCESSED_DIR.relative_to(ROOT).as_posix()
MANIFEST = MANIFEST_PATH.relative_to(ROOT).as_posix()
SYNTHETIC_NOTE = "Synthetic-data benchmark; these results do not establish real-world detection performance."
FORBIDDEN = {"is_illicit", "pattern_type", "scenario_id", "split", "is_licit_exchange"}


def label(value):
    return value.replace("_", " ").capitalize()


def count_items(counter):
    return [{"id": key, "label": label(key), "count": value}
            for key, value in sorted(counter.items(), key=lambda item: (-item[1], item[0]))]


def metrics(values, names):
    return [{"id": name, "label": name.replace("_", " ").upper(), "value": values[name]}
            for name in names]


def utc(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def iso(value):
    return value.isoformat().replace("+00:00", "Z")


def bucket_start(value, bucket):
    value = value.replace(hour=0, minute=0, second=0, microsecond=0)
    if bucket == "week":
        return value - timedelta(days=value.weekday())
    if bucket == "month":
        return value.replace(day=1)
    return value


def next_bucket(value, bucket):
    if bucket == "month":
        return (value.replace(day=28) + timedelta(days=4)).replace(day=1)
    return value + timedelta(days=7 if bucket == "week" else 1)


class ObservatoryService:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self._cache = {}
        self._lock = RLock()

    def _cached(self, key, sources, build):
        with self._lock:
            fingerprint = tuple((source, (self.root / source).stat().st_mtime_ns,
                                 (self.root / source).stat().st_size) for source in sources)
            cached = self._cache.get(key)
            if cached is None or cached[0] != fingerprint:
                value = build()
                # Do not publish a snapshot assembled during an artifact replacement.
                after = tuple((source, (self.root / source).stat().st_mtime_ns,
                               (self.root / source).stat().st_size) for source in sources)
                if after != fingerprint:
                    raise ValueError("Artifacts changed during aggregation; retry request")
                self._cache[key] = (fingerprint, value)
            return copy.deepcopy(self._cache[key][1])

    def _json(self, source):
        with (self.root / source).open(encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, dict):
            raise ValueError("Artifact must contain a JSON object")
        return value

    def _active(self):
        """Runtime ML manifest is the version selector; never pick a newer report implicitly."""
        manifest = self._cached("active_manifest", [MANIFEST], lambda: self._json(MANIFEST))
        binary = manifest.get("binary_model", "")
        typology = manifest.get("typology_model", "")
        if not isinstance(binary, str) or not isinstance(typology, str):
            raise ValueError("Missing active model names")
        import re
        match = re.fullmatch(r"binary_model_(v[0-9]+)\.ubj", binary)
        if not match or typology != f"typology_model_{match.group(1)}.ubj":
            raise ValueError("Unsupported or mismatched runtime model versions")
        version = match.group(1)
        if manifest.get("feature_count") != len(manifest.get("feature_names", [])) or FORBIDDEN.intersection(manifest["feature_names"]):
            raise ValueError("Invalid active feature schema")
        return version, manifest

    def _response(self, scope, sources, schema, build, notes=(), model="v9", dataset="V9.0 corrected"):
        meta = ObservatoryMeta(
            sources=sources, scope=scope, dataset_version=dataset, model_version=model,
            generated_at=iso(datetime.now(timezone.utc)), notes=list(notes),
        )
        try:
            data = schema.model_validate(build())
            return ObservatoryResponse[schema](status="available", meta=meta, data=data)
        except (OSError, ValueError, TypeError, KeyError, ImportError, AttributeError, IndexError, OverflowError) as exc:
            logger.warning("Observatory %s unavailable: %s", scope, exc)
            return ObservatoryResponse[schema](
                status="unavailable", meta=meta, data=None,
                message="Required local artifacts are missing, invalid or incompatible. See backend logs.",
            )

    def _report(self):
        def build():
            report = self._json(REPORT)
            ds = report["dataset"]
            if ds["version"] != "V9.0 corrected":
                raise ValueError("Unexpected benchmark dataset version")
            if ds["train_scenarios"] + ds["frozen_test_scenarios"] != ds["total_scenarios"]:
                raise ValueError("Inconsistent scenario totals")
            if ds["train_transactions"] + ds["test_transactions"] != ds["total_transactions"]:
                raise ValueError("Inconsistent transaction totals")
            if ds["scenario_overlap"] != 0 or ds["txid_overlap"] != 0:
                raise ValueError("Benchmark split overlap")
            cm = report["binary_evaluation"]["confusion_matrix"]
            if sum(cm.values()) != ds["frozen_test_scenarios"]:
                raise ValueError("Binary confusion matrix total mismatch")
            if cm["TP"] + cm["FN"] != ds["frozen_test_illicit"] or cm["TN"] + cm["FP"] != ds["frozen_test_licit"]:
                raise ValueError("Binary class support mismatch")
            typ = report["typology_evaluation"]
            classes, matrix = typ["confusion_matrix_classes"], typ["confusion_matrix"]
            if len(matrix) != len(classes) or any(len(row) != len(classes) for row in matrix):
                raise ValueError("Typology confusion matrix shape mismatch")
            for index, name in enumerate(classes):
                row = typ["per_class"][name]
                if sum(matrix[index]) != row["n_actual"] or sum(r[index] for r in matrix) != row["n_predicted"]:
                    raise ValueError("Typology support mismatch")
            if sum(map(sum, matrix)) != typ["illicit_scenarios"] or typ["illicit_scenarios"] != ds["frozen_test_illicit"]:
                raise ValueError("Typology confusion matrix total mismatch")
            return report
        return self._cached("report", [REPORT], build)

    def overview(self):
        try:
            version, manifest = self._active()
        except (OSError, ValueError, TypeError, KeyError) as exc:
            logger.warning("Observatory active manifest unavailable: %s", exc)
            version, manifest = "unknown", {}
        if version != "v9":
            return self._overview_runtime(version, manifest)
        def build():
            report = self._report()
            ds = report["dataset"]
            return dict(
                title="BitKaun Observatory", evaluation_date=report["evaluation_end"],
                transactions=ds["total_transactions"], scenarios=ds["total_scenarios"],
                train_scenarios=ds["train_scenarios"], test_scenarios=ds["frozen_test_scenarios"],
                features=report["feature_schema"]["count"],
                binary_model=report["models"]["binary"]["path"],
                typology_model=report["models"]["typology"]["path"],
                headline_metrics=metrics(report["binary_evaluation"], ["precision", "recall", "f1", "roc_auc"]),
                formal_decision=report["formal_decision"],
                sections=["dataset", "performance", "features", "pipeline", "patterns"],
            )
        return self._response("frozen_test_benchmark", [MANIFEST, REPORT], OverviewData, build,
                              [SYNTHETIC_NOTE, "Benchmark model metadata is not runtime model health or the active case."])

    def _overview_runtime(self, version, manifest):
        sources = [MANIFEST, f"ml/reports/binary_metrics_{version}.json", f"ml/reports/typology_metrics_{version}.json"]

        def build():
            if version not in {"v8"}:
                raise ValueError("No compatible saved evaluation for the active runtime model")
            binary = self._json(sources[1])["metrics"]
            typology = self._json(sources[2])
            if any(binary[key] != value for key, value in manifest["evaluation_metrics"]["binary"].items()):
                raise ValueError("Binary report does not match the active manifest")
            if any(typology[key] != value for key, value in manifest["evaluation_metrics"]["typology"].items()):
                raise ValueError("Typology report does not match the active manifest")
            snapshot = self._dataset_snapshot(self._dataset_sources())
            if snapshot["totals"]["scenarios"] != manifest["train_scenarios"] + manifest["test_scenarios"]:
                raise ValueError("Bundled dataset does not match the active model split")
            return dict(title="BitKaun Observatory", evaluation_date=manifest["timestamp"],
                        transactions=snapshot["totals"]["transactions"],
                        scenarios=snapshot["totals"]["scenarios"],
                        train_scenarios=manifest["train_scenarios"], test_scenarios=manifest["test_scenarios"],
                        features=manifest["feature_count"], binary_model=manifest["binary_model"],
                        typology_model=manifest["typology_model"],
                        headline_metrics=metrics(binary, ["precision", "recall", "f1", "roc_auc"]),
                        sections=["dataset", "performance", "features", "pipeline", "patterns"])
        return self._response("saved_test_benchmark", sources + self._dataset_sources(), OverviewData, build,
                              [SYNTHETIC_NOTE, "Metrics come from saved evaluation of the active runtime model."], model=version,
                              dataset=DATA_DIR)

    def performance(self):
        try:
            version, manifest = self._active()
        except (OSError, ValueError, TypeError, KeyError):
            version, manifest = "unknown", {}
        if version != "v9":
            return self._performance_runtime(version, manifest)
        def build():
            r = self._report()
            b, t = r["binary_evaluation"], r["typology_evaluation"]
            cm = b["confusion_matrix"]
            return dict(
                evaluation_date=r["evaluation_end"], evaluation_type=r["evaluation_type"], threshold=b["threshold"],
                binary=dict(sample_count=r["dataset"]["frozen_test_scenarios"],
                            metrics=metrics(b, ["precision", "recall", "f1", "accuracy", "balanced_accuracy", "roc_auc", "pr_auc"]),
                            confusion_matrix=dict(labels=["licit", "illicit"], values=[[cm["TN"], cm["FP"]], [cm["FN"], cm["TP"]]])),
                typology=dict(sample_count=t["illicit_scenarios"],
                              metrics=metrics(t, ["macro_f1", "weighted_f1", "accuracy", "balanced_accuracy", "ovr_roc_auc"]),
                              confusion_matrix=dict(labels=t["confusion_matrix_classes"], values=t["confusion_matrix"]),
                              per_class=[dict(id=name, label=label(name), precision=t["per_class"][name]["precision"],
                                              recall=t["per_class"][name]["recall"], f1=t["per_class"][name]["f1"],
                                              support=t["per_class"][name]["n_actual"], predicted_count=t["per_class"][name]["n_predicted"])
                                         for name in t["confusion_matrix_classes"]]),
                diagnostics=[
                    dict(id="size_only", label="Size-only audit", metrics=metrics(r["size_only_audit"], ["roc_auc", "pr_auc"]), note=r["size_only_audit"]["note"]),
                    dict(id="size_controlled", label="Size-controlled subset", metrics=metrics(r["size_controlled"], ["roc_auc", "pr_auc", "balanced_accuracy"]), note=f"Matched subset: {r['size_controlled']['retained_n']} scenarios."),
                    dict(id="moderate_shift", label="Moderate distribution shift", metrics=metrics(r["moderate_shift"], ["baseline_auc", "shifted_auc"]), note="Reported robustness diagnostic; not a model-version comparison."),
                    dict(id="calibration", label="Calibration diagnostics", metrics=metrics(r["calibration_gate_b"], ["raw_ece_10bin", "adaptive_ece_10bin", "brier_score"]), note="Lower is better. " + r["calibration_gate_b"]["note"]),
                ],
                formal_decision=r["formal_decision"],
                limitations=[SYNTHETIC_NOTE, r["size_only_audit"]["note"], r["typology_determinism"]["interpretation"]],
                curves_unavailable_reason="The frozen report contains scalar metrics, not ROC/PR coordinates or training history. No evaluation is rerun.",
            )
        return self._response("frozen_test_benchmark", [MANIFEST, REPORT], PerformanceData, build, [SYNTHETIC_NOTE])

    def _performance_runtime(self, version, manifest):
        sources = [MANIFEST, f"ml/reports/binary_metrics_{version}.json", f"ml/reports/typology_metrics_{version}.json",
                   f"{DATA_DIR}/scenario_labels_test.csv"]

        def build():
            if version != "v8":
                raise ValueError("No compatible saved evaluation for the active runtime model")
            binary = self._json(sources[1])
            typology = self._json(sources[2])
            b = binary["metrics"]
            if any(b[key] != value for key, value in manifest["evaluation_metrics"]["binary"].items()):
                raise ValueError("Binary report does not match the active manifest")
            if any(typology[key] != value for key, value in manifest["evaluation_metrics"]["typology"].items()):
                raise ValueError("Typology report does not match the active manifest")
            labels = list(self._rows(self.root / sources[3], {"scenario_id", "is_illicit"}))
            if len(labels) != manifest["test_scenarios"] or len({row["scenario_id"] for row in labels}) != len(labels):
                raise ValueError("Test scenario labels do not match the active manifest")
            if any(row["is_illicit"] not in {"0", "1"} for row in labels):
                raise ValueError("Invalid binary test labels")
            illicit_support = sum(row["is_illicit"] == "1" for row in labels)
            # V8 training script reports scalars only. Do not reconstruct a matrix from rounded metrics.
            return dict(evaluation_date=manifest["timestamp"], evaluation_type="Saved V8 held-out test metrics",
                        threshold=BINARY_ILLICIT_THRESHOLD, binary=dict(sample_count=manifest["test_scenarios"],
                                                    metrics=metrics(b, ["precision", "recall", "f1", "accuracy", "bacc", "roc_auc", "pr_auc"])),
                        typology=dict(sample_count=illicit_support,
                                      metrics=metrics(typology, ["macro_f1", "weighted_f1", "accuracy"])),
                        diagnostics=[dict(id="calibration", label="Saved calibration diagnostics",
                                          metrics=metrics(binary["calibration"], ["ece", "brier"]),
                                          note="Lower is better; saved evaluation scalars.")],
                        limitations=[SYNTHETIC_NOTE, "V8 reports do not contain confusion matrices or per-class precision/recall; no values are invented."],
                        curves_unavailable_reason="V8 saved reports contain scalar metrics, not ROC/PR coordinates or training history.")
        return self._response("saved_test_benchmark", sources, PerformanceData, build, [SYNTHETIC_NOTE],
                              model=version, dataset=DATA_DIR)

    @staticmethod
    def _dataset_sources():
        return [f"{DATA_DIR}/{split}_{kind}.csv" for split in ("train", "test") for kind in ("blockchain", "network")]

    @staticmethod
    def _rows(path, required):
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if not required.issubset(set(reader.fieldnames or [])):
                raise ValueError(f"Required columns missing in {path.name}")
            yield from reader

    def _dataset_snapshot(self, sources):
        def build():
            daily = defaultdict(lambda: [0, 0.0])
            wallets, all_txids, all_scenarios = set(), set(), set()
            scenario_classes, binary_classes, transaction_classes = Counter(), Counter(), Counter()
            infrastructure, countries, scripts = Counter(), Counter(), Counter()
            splits, first, last = [], None, None
            for split in ("train", "test"):
                txids, scenarios = set(), {}
                for row in self._rows(self.root / DATA_DIR / f"{split}_blockchain.csv", {
                    "txid", "timestamp", "input_addresses", "output_addresses", "output_amounts",
                    "scenario_id", "pattern_type", "is_illicit", "script_type",
                }):
                    txid, scenario = row["txid"], row["scenario_id"]
                    if not txid or not scenario or txid in all_txids or scenario in all_scenarios:
                        raise ValueError("Duplicate transaction or overlapping/empty scenario in dataset")
                    all_txids.add(txid)
                    txids.add(txid)
                    pattern = row["pattern_type"]
                    if row["is_illicit"] not in ("0", "1") or not pattern:
                        raise ValueError("Invalid dataset label")
                    binary = "illicit" if row["is_illicit"] == "1" else "licit"
                    if scenario in scenarios and scenarios[scenario] != (pattern, binary):
                        raise ValueError("Inconsistent scenario labels")
                    scenarios[scenario] = (pattern, binary)
                    timestamp = utc(row["timestamp"])
                    first = min(first, timestamp) if first else timestamp
                    last = max(last, timestamp) if last else timestamp
                    inputs, outputs = json.loads(row["input_addresses"]), json.loads(row["output_addresses"])
                    amounts = json.loads(row["output_amounts"])
                    if not all(isinstance(v, list) and v for v in (inputs, outputs, amounts)):
                        raise ValueError("Invalid ledger arrays")
                    if not all(isinstance(address, str) and address for address in inputs + outputs):
                        raise ValueError("Invalid wallet address")
                    if len(outputs) != len(amounts) or not all(isinstance(v, (float, int)) and not isinstance(v, bool) and math.isfinite(v) and v >= 0 for v in amounts):
                        raise ValueError("Invalid output amounts")
                    wallets.update(inputs + outputs)
                    day = bucket_start(timestamp, "day")
                    daily[day][0] += 1
                    daily[day][1] += math.fsum(amounts)
                    transaction_classes[pattern] += 1
                    scripts[row["script_type"] or "unknown"] += 1
                if not txids:
                    raise ValueError("Empty dataset split")
                all_scenarios.update(scenarios)
                for pattern, binary in scenarios.values():
                    scenario_classes[pattern] += 1
                    binary_classes[binary] += 1
                seen_network = set()
                for row in self._rows(self.root / DATA_DIR / f"{split}_network.csv", {"txid", "node_type", "country_code"}):
                    txid = row["txid"]
                    if txid not in txids or txid in seen_network:
                        raise ValueError("Network/ledger join is not one-to-one")
                    seen_network.add(txid)
                    infrastructure[row["node_type"] or "unknown"] += 1
                    countries[row["country_code"] or "unknown"] += 1
                if seen_network != txids:
                    raise ValueError("Network rows missing for ledger transactions")
                splits.append(dict(id=split, label=label(split), transactions=len(txids), scenarios=len(scenarios)))
            return dict(
                totals=dict(transactions=len(all_txids), scenarios=len(all_scenarios), unique_wallets=len(wallets),
                            first_timestamp=iso(first), last_timestamp=iso(last)),
                splits=splits, daily=dict(daily),
                scenario_class_distribution=count_items(scenario_classes),
                scenario_binary_distribution=count_items(binary_classes),
                transaction_class_distribution=count_items(transaction_classes),
                infrastructure_distribution=count_items(infrastructure), country_distribution=count_items(countries),
                script_distribution=count_items(scripts),
            )
        return self._cached("dataset", sources, build)

    def dataset(self, bucket="month"):
        sources = self._dataset_sources()

        def build():
            if bucket not in {"day", "week", "month"}:
                raise ValueError("Invalid timeline bucket")
            snapshot = self._dataset_snapshot(sources)
            grouped = defaultdict(lambda: [0, 0.0])
            for day, (count, volume) in snapshot.pop("daily").items():
                key = bucket_start(day, bucket)
                grouped[key][0] += count
                grouped[key][1] += volume
            current, end = min(grouped), max(grouped)
            timeline = []
            while current <= end:
                if len(timeline) >= 20000:
                    raise ValueError("Dataset exceeds the supported timeline range")
                count, volume = grouped[current]
                timeline.append(dict(timestamp=iso(current), transactions=count, output_volume_btc=round(volume, 8)))
                current = next_bucket(current, bucket)
            return dict(**snapshot, bucket=bucket, timeline=timeline)
        return self._response("bundled_dataset", sources, DatasetData, build, [
            SYNTHETIC_NOTE, "Counts are descriptive dataset labels, not model predictions. Train and test are combined.",
            "Output volume sums transaction outputs, including change and repeated hops; it is not unique funds or illicit volume.",
            "Naive source timestamps are interpreted as UTC. Weeks start Monday; empty interior buckets are zero-filled.",
        ], model=None, dataset=DATA_DIR)

    @staticmethod
    def _feature_group(name):
        if name in {"total_input_mean", "total_output_mean", "fee_ratio_mean", "fee_ratio_std", "amount_decay_slope", "output_amount_gini", "denomination_entropy", "round_number_ratio", "io_amount_similarity"}:
            return "financial"
        if name.startswith("prop_delta") or name in {"suspicious_infra_ratio", "unique_asn_count", "asn_concentration", "unique_country_count", "country_concentration", "unique_ip_count", "ip_to_addr_ratio", "alt_port_ratio", "unique_user_agents"}:
            return "network"
        if name.startswith("inter_tx") or name in {"time_span_hours", "burstiness_B", "hour_of_day_entropy"}:
            return "temporal"
        if name in {"script_type_entropy", "script_type_mode"}:
            return "script"
        if name in {"max_chain_length", "graph_density", "avg_clustering", "max_in_degree", "max_out_degree", "degree_assortativity", "edge_to_node_ratio"}:
            return "graph"
        return "structure"

    def features(self, model="binary", limit=15):
        try:
            version, manifest = self._active()
        except (OSError, ValueError, TypeError, KeyError):
            version, manifest = "unknown", {}
        source = f"ml/models/{model}_model_{version}.ubj"
        sources = [MANIFEST, source]

        def build():
            if model not in {"binary", "typology"} or not 1 <= limit <= 46:
                raise ValueError("Invalid feature selection")

            def extract():
                import xgboost as xgb
                names = manifest["feature_names"]
                if manifest[f"{model}_model"] != f"{model}_model_{version}.ubj":
                    raise ValueError("Feature contract does not match active model")
                if not names or len(set(names)) != len(names) or len(names) != manifest["feature_count"] or FORBIDDEN.intersection(names):
                    raise ValueError("Invalid feature contract")
                booster = xgb.Booster()
                try:
                    booster.load_model(self.root / source)
                    raw = booster.get_score(importance_type="gain")
                except xgb.core.XGBoostError as exc:
                    raise ValueError("Could not read model feature importance") from exc
                if booster.num_features() != len(names) or (booster.feature_names is not None and booster.feature_names != names):
                    raise ValueError("Model/feature schema mismatch")
                keys = names if booster.feature_names else [f"f{i}" for i in range(len(names))]
                if set(raw) - set(keys):
                    raise ValueError("Unknown model feature keys")
                scores = {name: float(raw.get(key, 0)) for name, key in zip(names, keys)}
                if any(not math.isfinite(v) or v < 0 for v in scores.values()) or sum(scores.values()) <= 0:
                    raise ValueError("Invalid model gain values")
                total = sum(scores.values())
                features = [dict(id=name, label=label(name), group=self._feature_group(name), importance=value / total)
                            for name, value in sorted(scores.items(), key=lambda item: (-item[1], item[0]))]
                groups = Counter()
                for item in features:
                    groups[item["group"]] += item["importance"]
                return dict(feature_count=len(names), features=features,
                            groups=[dict(id=name, label=label(name), group=name, importance=value)
                                    for name, value in sorted(groups.items(), key=lambda item: (-item[1], item[0]))])
            result = self._cached(f"features:{version}:{model}", sources, extract)
            result["features"] = result["features"][:limit]
            return dict(**result, model=model,
                        description="Average split gain per feature, normalized over all model features. Not SHAP, causal importance or a probability.",
                        local_shap_unavailable_reason="No benchmark-bound local SHAP example is published. This endpoint inspects model structure without inference.")
        return self._response("model_artifact", sources, FeatureData, build, [
            "Gain is extracted from the active runtime model file, not from a stored importance chart.",
            "Groups are presentation categories. Group sums use all features, even when the feature list is limited.",
        ], model=version, dataset=DATA_DIR)

    def pipeline(self):
        from backend.app.services.observatory_diagrams import pipeline
        return self._response("architecture", ["docs/V9_FINAL_ARCHITECTURE.md"], Diagram, pipeline,
                              ["Architecture diagram, not live processing progress."], dataset=None)

    def patterns(self):
        from backend.app.services.observatory_diagrams import patterns
        return self._response("illustration", ["docs/V9_FINAL_ARCHITECTURE.md", "GRAPH_ENGINE.md"], PatternsData,
                              patterns, ["Illustrative structures, not transactions, detected cases or evidence of criminality."], model=None, dataset=None)


observatory_service = ObservatoryService()
