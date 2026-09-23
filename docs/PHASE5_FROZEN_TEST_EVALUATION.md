# PHASE 5 — FINAL FROZEN-TEST EVALUATION REPORT

**Dataset:** V9.0 corrected (seed=20260921)
**Evaluated:** 2026-09-21T15:41 UTC
**Policy:** This evaluation was performed exactly once. The frozen test is now LOCKED.
**Architecture:** C (LOCKED)
**Decision threshold:** 0.50

---

## Pre-Evaluation Integrity Checks: 16/16 PASS

Frozen test composition: 448 illicit / 640 licit

---

## Binary Frozen-Test Evaluation

| Metric | Value | Gate A Req | Status |
|---|---|---|---|
| **ROC-AUC** | **0.997684** | >=0.985 | **PASS** |
| **PR-AUC** | **0.996915** | >=0.980 | **PASS** |
| **BAcc** | **0.976674** | >=0.940 | **PASS** |
| F1 | 0.974070 | — | — |
| Precision | 0.984055 | — | — |
| Recall | 0.964286 | — | — |
| Accuracy | 0.978860 | — | — |

Confusion matrix: TN=633 FP=7 FN=16 TP=432

---

## Calibration Diagnostics (Gate B — DIAGNOSTIC ONLY)

| Metric | Value | Note |
|---|---|---|
| Raw 10-bin ECE | 0.012712 | Gate B, diagnostic only |
| Adaptive ECE | 0.010753 | Gate B, diagnostic only |
| Brier score | 0.017688 | Gate B, diagnostic only |
| Cox slope | 0.0915 | INFO |
| Cox intercept | 0.4926 | INFO |

---

## Size-Only Audit

| Metric | Value | Req | Status |
|---|---|---|---|
| Size-only ROC-AUC | 0.870089 | <=0.580 | **FAIL** |
| Size-only PR-AUC | 0.844102 | <=0.450 | **FAIL** |
| Size-only max MI | 0.091894 | <=0.010 | **FAIL** |

Root cause: generator-level distribution imbalance between illicit and licit scenario sizes.
NOT a model-level problem (size-controlled test passes at AUC=0.998).

---

## Size-Controlled Test

| Metric | Value | Req | Status |
|---|---|---|---|
| Size-ctrl ROC-AUC | 0.997859 | >=0.960 | **PASS** |
| Size-ctrl PR-AUC | 0.997954 | >=0.960 | **PASS** |
| Size-ctrl BAcc | 0.977477 | >=0.880 | **PASS** |
| Size-ctrl F1 | 0.977169 | — | — |
| Retained scenarios | 888 (444 ill / 444 lit) | — | — |

---

## Moderate Size-Shift Test

| Metric | Value | Req | Status |
|---|---|---|---|
| Baseline AUC | 0.997684 | — | — |
| Shifted AUC (small scenarios, n=362) | 0.990245 | — | — |
| **delta_AUC** | **0.007439** | <=0.035 | **PASS** |

---

## Adversarial Size Inversion (Diagnostic Only)

| | Value |
|---|---|
| Adversarial model AUC (large-train, small-test) | 0.926302 |
| Corrected V9 model AUC | 0.997684 |
| delta_AUC (corrected - adversarial) | 0.071382 |

DIAGNOSTIC ONLY — not a formal acceptance criterion.

---

## Typology Frozen-Test Evaluation

448 illicit scenarios: ransomware=117, layering=115, peeling_chain=115, mixing=101

| Metric | Value | Gate A Req | Status |
|---|---|---|---|
| **Macro-F1** | **0.995546** | >=0.880 | **PASS** |
| Weighted-F1 | 0.995544 | — | — |
| Accuracy | 0.995536 | — | — |
| BAcc | 0.995351 | — | — |
| OvR ROC-AUC | 0.999986 | — | — |

Per-class: layering P=1.000 R=0.991 F1=0.996 | mixing P=1.000 R=0.990 F1=0.995 | peeling_chain P=1.000 R=1.000 F1=1.000 | ransomware P=0.983 R=1.000 F1=0.992

Confusion matrix:
```
              layering  mixing  peeling_chain  ransomware
layering(115):  114       0          0             1
mixing(101):      0     100          0             1
peeling_ch(115):  0       0        115             0
ransomware(117):  0       0          0           117
```

---

## Typology Determinism Diagnostic

Dev Macro-F1=1.000000 -> Frozen Macro-F1=0.995546, drop=0.004454
Generator remains highly deterministic on unseen synthetic scenarios.
Does NOT imply real-world typology separability.

---

## Binary Error Analysis (Descriptive Only)

FP=7 (all 'normal' licit) | FN=16 (all 'layering')
Layering FN fraction: 1.000 (16/16)
FN prob range: [0.026, 0.474], mean=0.248
FP prob range: [0.516, 0.964], mean=0.700

---

## Final Gate Table

| Gate | Metric | Req | Actual | Status | Type |
|---|---|---|---|---|---|
| A | ROC-AUC | >=0.985 | 0.997684 | PASS | FORMAL |
| A | PR-AUC | >=0.980 | 0.996915 | PASS | FORMAL |
| A | BAcc | >=0.940 | 0.976674 | PASS | FORMAL |
| A | Size-only ROC-AUC | <=0.580 | 0.870089 | **FAIL** | FORMAL |
| A | Size-only PR-AUC | <=0.450 | 0.844102 | **FAIL** | FORMAL |
| A | Size-only max MI | <=0.010 | 0.091894 | **FAIL** | FORMAL |
| A | Size-ctrl ROC-AUC | >=0.960 | 0.997859 | PASS | FORMAL |
| A | Size-ctrl PR-AUC | >=0.960 | 0.997954 | PASS | FORMAL |
| A | Size-ctrl BAcc | >=0.880 | 0.977477 | PASS | FORMAL |
| A | Moderate shift ΔAUC | <=0.035 | 0.007439 | PASS | FORMAL |
| A | Typology Macro-F1 | >=0.880 | 0.995546 | PASS | FORMAL |
| B | 10-bin ECE | <=0.010 | 0.012712 | FAIL | DIAGNOSTIC ONLY |
| B | Adaptive ECE | <=0.010 | 0.010753 | FAIL | DIAGNOSTIC ONLY |
| B | Brier score | <=0.015 | 0.017688 | FAIL | DIAGNOSTIC ONLY |
| B | Cox slope | ~1.0 | 0.0915 | INFO | DIAGNOSTIC ONLY |
| B | Cox intercept | ~0.0 | 0.4926 | INFO | DIAGNOSTIC ONLY |

---

## FORMAL DECISION

**FORMAL GATE A REQUIREMENTS NOT SATISFIED**

Failed requirements:
- Size-only ROC-AUC: 0.870089 > 0.580
- Size-only PR-AUC:  0.844102 > 0.450
- Size-only max MI:  0.091894 > 0.010

8 of 11 Gate A requirements pass. 3 fail (all in size-only audit).

Root cause: Generator-level distribution imbalance, not model reliance on size.
Evidence: Size-controlled test passes at ROC-AUC=0.998, ΔAUC shift=0.0074.

Recommended governance actions (requires explicit approval before action):
1. Reinterpret size-only gate as generator quality metric for synthetic data.
2. V9.1 generator study to equalize size distributions.
3. Size feature ablation study to demonstrate size is not load-bearing.

---

## Governance

Frozen test: EVALUATED EXACTLY ONCE — NOW PERMANENTLY LOCKED.
No model, threshold, feature, calibration, generator, or dataset changes
may be made based on this result without a new explicitly governed experiment.
