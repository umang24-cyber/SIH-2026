# Archived Scripts

These scripts were successfully migrated to the final production ML pipeline (`train_production.py`) on 2026-09-04 and are now obsolete.

| old file | purpose | still needed? | replacement | safe to archive? |
| --- | --- | --- | --- | --- |
| `03_train_binary.py` | Binary XGBoost training | No | `train_production.py` (Phase 4, 5, 6, 11) | Yes |
| `04_train_typology.py` | Typology XGBoost training | No | `train_production.py` (Phase 7, 9) | Yes |
| `05_ablation.py` | Feature-group ablation | No | `train_production.py` (Phase 6, 8) | Yes |
| `audit_v5.py` | V5 Gate auditor | No | Superseded by V6 methodology | Yes |
| `audit_v6.py` | V6 Gate auditor | No | Superseded by feature-group ablation | Yes |
| `full_audit_v3.py` | V3 shortcut audit | No | Obsolete | Yes |
| `diag_audit.py` | Diagnostic throwaway audit | No | Obsolete | Yes |

All functionality has been preserved and integrated into the safe, deterministic V6 production pipeline.
