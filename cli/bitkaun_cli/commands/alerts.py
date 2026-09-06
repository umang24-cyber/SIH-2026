"""
Alerts command for BitKaun CLI.
Renders prioritized AML forensic alerts sorted by confidence descending,
with ML typology predictions and SHAP explainability dossiers.
"""

from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, format_severity, warning_panel, error_panel


def render_alert_evidence(candidate_id: str):
    """Render deep SHAP evidence dossier for a specific alert candidate."""
    evidence = client.get_alert_evidence(candidate_id)
    if not evidence:
        error_panel(
            "Evidence Not Found",
            f"No forensic evidence record found for candidate '{candidate_id}'."
        )
        return

    scenario = evidence.get("scenario_id", "N/A")
    pattern = evidence.get("predicted_pattern_type", "N/A")
    bin_conf = evidence.get("binary_confidence", 0.0)
    typ_conf = evidence.get("typology_confidence", 0.0)
    heuristic = evidence.get("typology_heuristic_match", False)
    explanation = evidence.get("typology_explanation", "No explanation available.")

    console.print()
    console.print(
        Panel(
            f"[bold white]Candidate ID:[/] [bold cyan]{candidate_id}[/]\n"
            f"[dim]Scenario ID:[/]  [yellow]{scenario}[/]   "
            f"[dim]Predicted Pattern:[/] [bold red]{pattern.upper()}[/]\n"
            f"[dim]Binary Risk Confidence:[/]   [bold yellow]{bin_conf * 100:.1f}%[/]   "
            f"[dim]Typology Confidence:[/] [bold yellow]{typ_conf * 100:.1f}%[/]\n"
            f"[dim]Heuristic Corroboration:[/] [white]{'YES' if heuristic else 'NO'}[/]\n\n"
            f"[bold white]Forensic Rationale:[/bold white]\n[white]{explanation}[/white]",
            title="[bold green][*] DEEP FORENSIC EVIDENCE & SHAP ATTRIBUTION DOSSIER[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    # SHAP Attributions Table
    shap_list = evidence.get("ml_feature_attributions") or evidence.get("typology_shap_attributions") or []
    if shap_list:
        shap_table = Table(
            title="[bold green][*] XGBoost / TreeSHAP Feature Attribution Breakdown[/bold green]",
            box=box.ROUNDED,
            border_style="green",
            header_style="bold green on black",
            expand=True,
        )
        shap_table.add_column("Forensic Feature", style="cyan")
        shap_table.add_column("Feature Value", justify="right", style="white")
        shap_table.add_column("SHAP Impact Score", justify="right", style="yellow")
        shap_table.add_column("Direction / Risk Influence", justify="center")

        for item in shap_list[:10]:
            if isinstance(item, dict):
                feat = item.get("feature_name", "")
                val = item.get("value", "")
                sval = float(item.get("shap_value", 0.0))
                direction = item.get("direction", "RISK_INCREASING")
            elif isinstance(item, (list, tuple)):
                feat, sval = item[0], float(item[1])
                val = ""
                direction = "RISK_INCREASING" if sval > 0 else "RISK_DECREASING"
            else:
                continue

            dir_badge = (
                "[bold red]▲ ELEVATES RISK[/bold red]"
                if "INCREASING" in str(direction).upper() or sval > 0
                else "[bold green]▼ LOWERS RISK[/bold green]"
            )
            shap_table.add_row(
                feat,
                f"{val:.4f}" if isinstance(val, (int, float)) else str(val),
                f"{sval:+.4f}",
                dir_badge,
            )

        console.print(shap_table)

    # Telemetry Summary
    telem = evidence.get("telemetry_summary") or {}
    if telem:
        ips = ", ".join(telem.get("origin_ips", [])) or "None"
        asns = ", ".join(telem.get("origin_asns", [])) or "None"
        countries = ", ".join(telem.get("countries", [])) or "None"
        infra = telem.get("infrastructure_distribution", {})
        infra_str = ", ".join(f"{k}: {v}" for k, v in infra.items()) if infra else "None"

        console.print(
            Panel(
                f"[dim]Origin IPs:[/]   [cyan]{ips}[/cyan]\n"
                f"[dim]Origin ASNs:[/]  [yellow]{asns}[/yellow]\n"
                f"[dim]Countries:[/]    [white]{countries}[/white]\n"
                f"[dim]Infrastructure Nodes:[/] [bold magenta]{infra_str}[/bold magenta]",
                title="[bold green][*] P2P Telemetry & Infrastructure Provenance[/bold green]",
                border_style="green",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )

    console.print()


def execute(args: list[str] = None):
    """Execute the alerts command."""
    # Check for --detail or -d flag
    if args:
        if args[0] in ("--detail", "-d") and len(args) > 1:
            render_alert_evidence(args[1].strip())
            return
        elif args[0].startswith("cand_"):
            render_alert_evidence(args[0].strip())
            return

    # Fetch alerts
    limit = 25
    if args and len(args) >= 2 and args[0] in ("--limit", "-l"):
        try:
            limit = int(args[1])
        except ValueError:
            pass

    data = client.get_alerts(limit=limit)
    if not data:
        return

    alerts_list = data.get("alerts", [])
    total = data.get("total_alerts", len(alerts_list))

    if not alerts_list:
        warning_panel("No Alerts", "Zero forensic candidate alerts are currently active.")
        return

    # Sort alerts by risk_score or binary_confidence descending
    sorted_alerts = sorted(
        alerts_list,
        key=lambda a: float(a.get("risk_score") or a.get("binary_confidence") or 0.0),
        reverse=True,
    )

    console.print()
    console.print(
        Panel(
            f"[bold white]Active Alerts Monitored:[/] [bold red]{total:,}[/bold red]   "
            f"[dim]Displaying Top:[/] [bold yellow]{len(sorted_alerts)}[/bold yellow]\n"
            f"[dim]Tip: Inspect full evidence with[/dim] [cyan]alerts --detail <candidate_id>[/cyan]",
            title="[bold green][*] PRIORITIZED AML FORENSIC ALERT FEED[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(0, 2),
        )
    )

    table = Table(
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
        expand=True,
    )
    table.add_column("Rank", style="bold yellow", justify="center")
    table.add_column("Candidate ID", style="cyan")
    table.add_column("Pattern Type", justify="center")
    table.add_column("Confidence", justify="right", style="yellow")
    table.add_column("Severity", justify="center")
    table.add_column("Forensic Explanation", style="white")

    for rank, alert in enumerate(sorted_alerts, 1):
        cid = alert.get("candidate_id", "N/A")
        pattern = alert.get("predicted_pattern_type", "unknown").upper()
        conf = float(alert.get("typology_confidence") or alert.get("binary_confidence") or 0.0)
        sev = alert.get("severity", "MEDIUM")
        explanation = alert.get("explanation", "No explanation available.")

        pattern_badge = f"[bold cyan]{pattern}[/bold cyan]"
        if pattern == "RANSOMWARE":
            pattern_badge = f"[bold white on red] {pattern} [/bold white on red]"
        elif pattern == "MIXING":
            pattern_badge = f"[bold black on bright_magenta] {pattern} [/bold black on bright_magenta]"
        elif pattern == "LAYERING":
            pattern_badge = f"[bold black on yellow] {pattern} [/bold black on yellow]"

        table.add_row(
            f"#{rank}",
            cid,
            pattern_badge,
            f"{conf * 100:.1f}%",
            format_severity(sev),
            explanation,
        )

    console.print(table)
    console.print()
