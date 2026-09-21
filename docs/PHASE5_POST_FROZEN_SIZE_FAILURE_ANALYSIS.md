# PHASE 5 — POST-FROZEN SIZE FAILURE ANALYSIS

**Status:** V9.0 Frozen Test is PERMANENTLY LOCKED.
**Objective:** Diagnose the root cause of the V9 Gate A size-only failure using only training/development data and generator source code inspection.

---

## 1. V9 Frozen-Test Formal Decision Summary

- **Decision:** FORMAL GATE A REQUIREMENTS **NOT SATISFIED**.
- **Failed Gates:**
  1. Size-only ROC-AUC (0.870089 > 0.580)
  2. Size-only PR-AUC (0.844102 > 0.450)
  3. Size-only max MI (0.091894 > 0.010)
- **Passed Gates:**
  - Binary classification performance (ROC-AUC=0.9977)
  - Size-controlled test (ROC-AUC=0.9979)
  - Moderate size shift test (ΔAUC=0.0074)
  - Typology classification (Macro-F1=0.9955)

---

## 2. Root Cause of Size-Only Failure

The size-only audit evaluates the 9 features in the `SIZE_FEATS` list (e.g., `total_input_mean`, `amount_decay_slope`, `round_number_ratio`).

**The root cause is AMOUNT and DENOMINATION scaling, NOT transaction count.** 

In V9, we successfully fixed the `num_txns` distribution. A model trained *only* on `num_txns` achieves an uninformative AUC of **0.5082**. The transaction count distributions are heavily overlapping between classes.

However, the generator mechanically links **monetary amounts** to the typology structures. The size-only failure is driven entirely by these artifactual amount-based proxies. On the training data, the 9 size features achieve an AUC of **0.8876**, driven by:
1. `round_number_ratio` (Univariate AUC = 0.631)
2. `amount_decay_slope` (Univariate AUC = 0.697)
3. `total_output_mean` (Univariate AUC = 0.526)

---

## 3. Exact Generator Mechanisms Responsible

Inspection of `data_pipeline/generate_v9.py` reveals the exact mechanical shortcuts:

### A. The `round_number_ratio` Shortcut (Mixing)
In `_gen_mixing`, CoinJoin scenarios are generated using strict fixed integer denominations:
```python
denoms = [1_000_000, 2_000_000, 5_000_000, 10_000_000, 50_000_000]
```
These perfectly align with the `ROUND_TARGETS` (0.01, 0.02, 0.05, 0.1, 0.5 BTC) used to calculate `round_number_ratio` in feature engineering. Licit scenarios use random lognormal amounts. Thus, `round_number_ratio` deterministically flags mixing scenarios.

### B. The `amount_decay_slope` Shortcut (Peeling Chains)
In `_gen_peeling`, the entire chain is funded by a single initial pool:
```python
cb = _amt_sat(rng) * 3
```
Each hop peels off a fraction (`30-70%`), carrying the remainder forward. This creates a geometrically decaying output amount over time. `amount_decay_slope` perfectly captures this structural decay, which licit scenarios (which randomly inject new funds) never exhibit.

### C. The `total_input_mean` Shortcut (Amount Dilution)
Because Peeling and Layering typologies split a fixed starting balance over $N$ transactions without injecting new funds, their average transaction amount is artificially tiny ($1/N$). 
- **Licit Mean Input:** 1.29 BTC
- **Ransomware Mean Input:** 1.64 BTC
- **Peeling Chain Mean Input:** 0.30 BTC

---

## 4. Why the Size-Controlled Test Passed

The frozen-test size-controlled audit (which achieved AUC=0.998) matched scenarios based **only on transaction count (`num_txns`) deciles**. 

It did **not** control for amount proxies. Because a peeling chain of $N=30$ and a licit scenario of $N=30$ have completely different `amount_decay_slope` and `round_number_ratio` values, the full model could still leverage these shortcuts (alongside legitimate graph features) to perfectly classify the controlled holdout set.

Thus, the size-controlled test proved the model doesn't rely on transaction count, but it **did not prove the model relies solely on behavioral structure**, as amount shortcuts remained perfectly intact.

---

## 5. Proposed V9.1 Generator Correction

To fix the amount-size shortcuts without destroying legitimate behavioral topologies, V9.1 must implement the following:

1. **Balance Amount Injection:**
   - In `_gen_peeling` and `_gen_layering`, scale the initial funding pool by $N$ (e.g., `_amt_sat(rng) * (N / 3)`) so that the *average* transaction amount matches the licit distribution (~1.2 BTC), preventing dilution shortcuts.
2. **Obfuscate Denominations:**
   - Do NOT remove strict denominations from mixing, as CoinJoins *mechanically require* equal denominations for anonymity.
   - Instead, **inject round numbers into licit scenarios**. Simulate retail payments or exchange withdrawals in `_gen_licit` that use the exact same `denoms` list. This ensures `round_number_ratio` exists in both classes: $P(\text{round\_number} | \text{licit}) \approx P(\text{round\_number} | \text{illicit})$.
3. **Decay Slope Masking:**
   - Ensure licit scenarios occasionally exhibit structured spending decay (e.g., simulating a user spending down a wallet balance over time without replenishment) to mask the peeling chain slope.

---

## 6. Pre-Generation V9.1 Acceptance Criteria

Before a new V9.1 dataset can be approved for training, the generator must pass the following checks on a diagnostic sample:

1. **Size-Only AUC Gate:** A model trained on the 9 `SIZE_FEATS` must achieve ROC-AUC $\le 0.580$.
2. **Univariate Leakage Gates:**
   - `amount_decay_slope` Univariate AUC $\le 0.58$
   - `round_number_ratio` Univariate AUC $\le 0.58$
   - `total_input_mean` Univariate AUC $\le 0.58$
3. **Distribution Overlap:**
   - KS Statistic for `total_input_mean` (Licit vs Illicit) $\le 0.20$
   - KS Statistic for `num_txns` $\le 0.20$

---

## 7. Governance Status

> [!CAUTION]
> - V9.0 frozen test remains **LOCKED**.
> - No V9.0 model, dataset, or test modification occurred during this analysis.
> - **DO NOT generate V9.1 yet.**
> - **DO NOT retrain.**
> 
> The next step requires explicit governance approval of the V9.1 generator design and pre-generation tests.
