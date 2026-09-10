"""
FastAPI Routes for BitKaun Forensic Case Management.
Unified across Web UI (localhost), PowerShell, and Ubuntu CLI.
All cases are stored in the central `cases/` workspace directory.
"""
import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from backend.app.core.config import CASES_DIR

router = APIRouter(prefix="/cases", tags=["Case Management"])

ACTIVE_CASE_FILE = CASES_DIR / ".active_case"


class InitCaseRequest(BaseModel):
    case_name: str


class SetActiveCaseRequest(BaseModel):
    case_name: str


class SaveArtifactRequest(BaseModel):
    command_name: str
    identifier: str
    data: Any
    subfolder: str = "reports"  # reports, dossiers, or evidence


def _get_active_case_name() -> Optional[str]:
    """Reads the active case name from cases/.active_case."""
    if ACTIVE_CASE_FILE.is_file():
        try:
            name = ACTIVE_CASE_FILE.read_text(encoding="utf-8").strip()
            if name and (CASES_DIR / name).is_dir():
                return name
        except Exception:
            pass
    return None


def _set_active_case_name(name: Optional[str]):
    """Writes or clears the active case name in cases/.active_case."""
    if not name:
        if ACTIVE_CASE_FILE.is_file():
            try:
                ACTIVE_CASE_FILE.unlink()
            except Exception:
                ACTIVE_CASE_FILE.write_text("", encoding="utf-8")
    else:
        ACTIVE_CASE_FILE.write_text(name.strip(), encoding="utf-8")


def _list_case_folders() -> List[Dict[str, Any]]:
    """Scans CASES_DIR for folders containing .bitkaun/case.json."""
    if not CASES_DIR.is_dir():
        return []

    active_name = None
    if ACTIVE_CASE_FILE.is_file():
        try:
            active_name = ACTIVE_CASE_FILE.read_text(encoding="utf-8").strip()
        except Exception:
            pass

    case_items = []
    for item in sorted(CASES_DIR.iterdir(), key=lambda p: p.stat().st_mtime if p.is_dir() else 0, reverse=True):
        if not item.is_dir() or item.name.startswith("."):
            continue
        case_json_file = item / ".bitkaun" / "case.json"
        if not case_json_file.is_file():
            continue

        try:
            with open(case_json_file, "r", encoding="utf-8") as f:
                case_meta = json.load(f)
        except Exception:
            case_meta = {"case_name": item.name}

        reports_dir = item / "reports"
        dossiers_dir = item / "dossiers"
        evidence_dir = item / "evidence"

        r_count = len(list(reports_dir.glob("*.json"))) if reports_dir.is_dir() else 0
        d_count = len(list(dossiers_dir.glob("*.json"))) if dossiers_dir.is_dir() else 0
        e_count = len(list(evidence_dir.iterdir())) if evidence_dir.is_dir() else 0

        case_items.append({
            "case_name": case_meta.get("case_name", item.name),
            "created_at": case_meta.get("created_at", "N/A"),
            "path": str(item.resolve()),
            "reports_count": r_count,
            "dossiers_count": d_count,
            "evidence_count": e_count,
            "total_artifacts": r_count + d_count + e_count,
            "is_active": (item.name == active_name)
        })

    return case_items


@router.get("")
def list_cases():
    """List all available forensic cases in the central workspace cases/ folder."""
    cases = _list_case_folders()
    active_name = _get_active_case_name()
    return {
        "status": "success",
        "cases_root": str(CASES_DIR.resolve()),
        "active_case": active_name,
        "total_cases": len(cases),
        "cases": cases
    }


@router.get("/active")
def get_active_case():
    """Retrieve details and statistics for the currently active forensic case."""
    active_name = _get_active_case_name()
    if not active_name:
        return {
            "status": "no_active_case",
            "message": "No active forensic case selected. Run `bitkaun init <case_name>` to begin."
        }

    case_dir = CASES_DIR / active_name
    case_json_file = case_dir / ".bitkaun" / "case.json"
    if not case_json_file.is_file():
        raise HTTPException(status_code=404, detail=f"Case '{active_name}' directory corrupted or missing case.json")

    with open(case_json_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    reports_dir = case_dir / "reports"
    dossiers_dir = case_dir / "dossiers"
    evidence_dir = case_dir / "evidence"

    r_count = len(list(reports_dir.glob("*.json"))) if reports_dir.is_dir() else 0
    d_count = len(list(dossiers_dir.glob("*.json"))) if dossiers_dir.is_dir() else 0
    e_count = len(list(evidence_dir.iterdir())) if evidence_dir.is_dir() else 0

    return {
        "status": "success",
        "case_name": meta.get("case_name", active_name),
        "created_at": meta.get("created_at", "N/A"),
        "location": str(case_dir.resolve()),
        "linked_scenarios": meta.get("linked_scenarios", []),
        "linked_addresses": meta.get("linked_addresses", []),
        "counts": {
            "reports": r_count,
            "dossiers": d_count,
            "evidence": e_count,
            "total": r_count + d_count + e_count
        }
    }


@router.post("/active")
def set_active_case(payload: SetActiveCaseRequest):
    """Set the active forensic case across all terminals and web UI, or clear with '..' / 'main' / 'none'."""
    case_name = payload.case_name.strip()
    if not case_name or case_name.lower() in ("none", "unset", "main", "..", "~", "exit"):
        _set_active_case_name(None)
        return {
            "status": "success",
            "message": "Active case cleared. Returned to workspace master.",
            "case_name": None
        }

    case_dir = CASES_DIR / case_name
    if not case_dir.is_dir() or not (case_dir / ".bitkaun" / "case.json").is_file():
        raise HTTPException(status_code=404, detail=f"Case '{case_name}' not found in {CASES_DIR}")

    _set_active_case_name(case_name)
    return {
        "status": "success",
        "message": f"Active case set to '{case_name}'",
        "case_name": case_name
    }


@router.delete("/active")
def delete_active_case():
    """Clear the currently selected active case."""
    _set_active_case_name(None)
    return {
        "status": "success",
        "message": "Active case cleared."
    }


@router.post("/init")
def init_case(payload: InitCaseRequest):
    """
    Initialize a new forensic case folder in the central cases/ workspace directory.
    Sets this newly created case as the active case immediately.
    """
    clean_name = re.sub(r'[\\/*?:"<>|\s]', '_', payload.case_name.strip())
    if not clean_name:
        raise HTTPException(status_code=400, detail="Invalid case name provided.")

    case_dir = CASES_DIR / clean_name
    dot_bitkaun = case_dir / ".bitkaun"
    reports_dir = case_dir / "reports"
    dossiers_dir = case_dir / "dossiers"
    evidence_dir = case_dir / "evidence"

    # Create directories
    dot_bitkaun.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    dossiers_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    case_json_path = dot_bitkaun / "case.json"
    created_at = datetime.now(timezone.utc).isoformat()
    case_metadata = {
        "case_name": clean_name,
        "created_at": created_at,
        "linked_scenarios": [],
        "linked_addresses": []
    }

    with open(case_json_path, "w", encoding="utf-8") as f:
        json.dump(case_metadata, f, indent=2)

    # Set as active
    _set_active_case_name(clean_name)

    return {
        "status": "success",
        "case_name": clean_name,
        "location": str(case_dir.resolve()),
        "created_at": created_at,
        "message": f"Forensic investigation case '{clean_name}' successfully initialized."
    }


@router.get("/{case_name}/ls")
def get_case_artifacts(case_name: str):
    """List all artifacts (reports, dossiers, evidence) in the specified case."""
    target_name = case_name.strip()
    if target_name.lower() in ("active", "current"):
        active = _get_active_case_name()
        if not active:
            raise HTTPException(status_code=404, detail="No active case currently selected.")
        target_name = active

    case_dir = CASES_DIR / target_name
    if not case_dir.is_dir() or not (case_dir / ".bitkaun" / "case.json").is_file():
        raise HTTPException(status_code=404, detail=f"Case '{target_name}' not found.")

    artifacts = []
    folders = [
        ("reports", "REPORT / TELEMETRY"),
        ("dossiers", "LEGAL DOSSIER"),
        ("evidence", "RAW EVIDENCE")
    ]

    for sub, label in folders:
        folder_path = case_dir / sub
        if not folder_path.is_dir():
            continue
        for file in sorted(folder_path.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True):
            if not file.is_file():
                continue
            st = file.stat()
            size = st.st_size
            if size >= 1024 * 1024:
                size_fmt = f"{size / (1024 * 1024):.1f} MB"
            elif size >= 1024:
                size_fmt = f"{size / 1024:.1f} KB"
            else:
                size_fmt = f"{size} B"

            saved_dt = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

            artifacts.append({
                "filename": file.name,
                "type": label,
                "folder": f"{sub}/",
                "size_bytes": size,
                "size": size_fmt,
                "saved_date": saved_dt,
                "path": str(file.resolve())
            })

    return {
        "status": "success",
        "case_name": target_name,
        "case_dir": str(case_dir.resolve()),
        "total_artifacts": len(artifacts),
        "artifacts": artifacts
    }


@router.post("/{case_name}/save")
def save_case_artifact(case_name: str, payload: SaveArtifactRequest):
    """Save an evidence or analytical output into the case's reports/ or dossiers/ directory."""
    target_name = case_name.strip()
    if target_name.lower() in ("active", "current"):
        active = _get_active_case_name()
        if not active:
            raise HTTPException(status_code=404, detail="No active case currently selected.")
        target_name = active

    case_dir = CASES_DIR / target_name
    if not case_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Case '{target_name}' does not exist.")

    subfolder = "dossiers" if payload.subfolder.lower() == "dossiers" else "reports"
    target_dir = case_dir / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_cmd = re.sub(r'[\\/*?:"<>|\s]', '_', str(payload.command_name).strip().lower())
    clean_id = re.sub(r'[\\/*?:"<>|\s]', '_', str(payload.identifier).strip())
    if not clean_id:
        clean_id = "export"

    filename = f"{clean_cmd}_{clean_id}_{timestamp}.json"
    out_path = target_dir / filename

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload.data, f, indent=2, ensure_ascii=False)

    return {
        "status": "success",
        "case_name": target_name,
        "filename": filename,
        "subfolder": subfolder,
        "path": str(out_path.resolve()),
        "relative_path": f"{subfolder}/{filename}"
    }
