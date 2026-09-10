"""
Case context manager for BitKaun CLI.
Manages forensic case directories in the private local AppData store
(%LOCALAPPDATA%/BitKaun/cases on Windows, /mnt/c/... or ~/.local/share on WSL2).
Ensures zero Git bloat and instant cross-platform synchronization.
"""

import json
import os
import platform
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from .render import console


def get_app_data_cases_dir() -> Path:
    """Returns OS-specific local application data cases directory (private to user profile)."""
    system = platform.system()
    if system == "Windows":
        app_data = os.getenv("LOCALAPPDATA")
        if not app_data:
            app_data = os.path.expanduser("~\\AppData\\Local")
        p = Path(app_data) / "BitKaun" / "cases"
    else:
        win_users = Path("/mnt/c/Users")
        if win_users.is_dir():
            for u in win_users.iterdir():
                target = u / "AppData" / "Local" / "BitKaun" / "cases"
                if target.is_dir():
                    return target
        p = Path.home() / ".local" / "share" / "BitKaun" / "cases"
    p.mkdir(parents=True, exist_ok=True)
    return p


def find_cases_dir() -> Path:
    """Find the central workspace `cases/` directory, always prioritizing private AppData."""
    app_data_cases = get_app_data_cases_dir()
    if app_data_cases.is_dir():
        return app_data_cases

    # Fallback to repo directory if AppData is somehow unavailable
    curr = Path.cwd().resolve()
    while True:
        candidate = curr / "cases"
        if candidate.is_dir():
            return candidate
        parent = curr.parent
        if parent == curr:
            break
        curr = parent

    return app_data_cases


def _load_case_dict(case_path: Path) -> Optional[Dict[str, Any]]:
    """Helper to parse and return case metadata dictionary from a case folder."""
    case_json_file = case_path / ".bitkaun" / "case.json"
    if not case_json_file.is_file():
        return None
    try:
        with open(case_json_file, "r", encoding="utf-8") as f:
            case_data = json.load(f)
        return {
            "case_root": case_path,
            "case_dir": case_path,
            "dot_bitkaun": case_path / ".bitkaun",
            "case_json_path": case_json_file,
            "reports_dir": case_path / "reports",
            "dossiers_dir": case_path / "dossiers",
            "evidence_dir": case_path / "evidence",
            "case_data": case_data,
            "case_name": case_data.get("case_name", case_path.name),
            "created_at": case_data.get("created_at", "N/A"),
        }
    except Exception:
        return None


def find_active_case() -> Optional[Dict[str, Any]]:
    """
    Find the currently active forensic case.
    Prioritizes the central AppData .active_case pointer so that cases
    are always managed in the private OS AppData store across all terminals and web UI.
    """
    cases_dir = find_cases_dir()

    # 1. Prioritize central cases/ directory .active_case pointer
    if cases_dir and cases_dir.is_dir():
        active_file = cases_dir / ".active_case"
        if active_file.is_file():
            try:
                active_name = active_file.read_text(encoding="utf-8").strip()
                if active_name:
                    target_case = cases_dir / active_name
                    result = _load_case_dict(target_case)
                    if result:
                        return result
            except Exception:
                pass
            # If .active_case file is explicitly empty or cleared, user exited case
            return None

    # 3. Fallback to CWD walking up (Git mental model)
    curr = Path.cwd().resolve()
    while True:
        result = _load_case_dict(curr)
        if result:
            return result
        parent = curr.parent
        if parent == curr:
            break
        curr = parent

    return None


def save_to_active_case(
    command_name: str,
    identifier: str,
    data: Any,
    subfolder: str = "reports"
) -> Optional[Path]:
    """
    Saves forensic command data to the active case's reports/ or dossiers/ subfolder.
    If no active case is found, prints a clear error message and refuses to save anywhere else.
    """
    case = find_active_case()
    if not case:
        console.print(
            "[bold red][X] No active case — run `bitkaun init <name>` to begin an investigation[/bold red]"
        )
        return None

    target_dir = case["dossiers_dir"] if subfolder == "dossiers" else case["reports_dir"]
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_cmd = re.sub(r'[\\/*?:"<>|\s]', '_', str(command_name).strip().lower())
    clean_id = re.sub(r'[\\/*?:"<>|\s]', '_', str(identifier).strip())
    if not clean_id:
        clean_id = "export"

    filename = f"{clean_cmd}_{clean_id}_{timestamp}.json"
    out_path = target_dir / filename

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Display clean path
        try:
            display_path = out_path.relative_to(case["case_root"])
        except Exception:
            display_path = out_path
        
        console.print(
            f"[bold green][✓] Saved {command_name} artifact to active case:[/] [bold cyan]{display_path}[/bold cyan]"
        )
        return out_path
    except Exception as exc:
        console.print(f"[bold red][X] Failed to save case artifact:[/] {exc}")
        return None
