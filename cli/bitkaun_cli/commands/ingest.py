"""
Ingest command for BitKaun CLI.
Injects synthetic attack models or raw custom UTXO JSON payloads into the live graph.
"""

import json
from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, format_btc, warning_panel, error_panel


def execute(args: list[str] = None):
    """Execute the ingest command."""
    if not args or args[0] in ("help", "-h", "--help"):
        console.print(
            Panel(
                "[bold green]BITKAUN DYNAMIC TRANSACTION INGESTION ENGINE[/bold green]\n\n"
                "[bold white]1. Sample Typology Injection:[/bold white]\n"
                "   [cyan]ingest sample ransomware[/cyan]\n"
                "   [cyan]ingest sample peeling[/cyan]\n"
                "   [cyan]ingest sample mixing[/cyan]\n"
                "   [cyan]ingest sample normal[/cyan]\n\n"
                "[bold white]2. Custom JSON Payload Ingestion:[/bold white]\n"
                "   [cyan]ingest {\"inputs\": [\"14c55RuJw...\"], \"outputs\": [{\"address\": \"1Qjw4un...\", \"amount\": 2.5}]}[/cyan]",
                title="[bold green][*] Ingestion Manual[/bold green]",
                border_style="green",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        return

    subcmd = args[0].strip().lower()

    # Case 1: Ingest sample
    if subcmd == "sample":
        if len(args) < 2:
            warning_panel("Missing Sample Type", "Specify: ransomware, peeling, mixing, or normal")
            return
        stype = args[1].strip().lower()
        data = client.ingest_sample(stype)
        if not data:
            return

        txid = data.get("transaction", {}).get("txid", "-")
        risk = data.get("risk_assessment", {})
        typo = risk.get("predicted_typology", "UNKNOWN").upper()
        p_risk = risk.get("risk_score", 0.0) * 100
        anom = risk.get("anomaly_score", 0.0)

        console.print()
        console.print(
            Panel(
                f"[dim]Sample Injected:[/]   [bold cyan]{stype.upper()}[/]\n"
                f"[dim]Assigned TxID:[/]     [bold yellow]{txid}[/]\n"
                f"[dim]XGBoost Risk:[/]      [bold red]{p_risk:.1f}%[/]   "
                f"[dim]Typology:[/]   [bold yellow]{typo}[/]\n"
                f"[dim]Anomaly Rating:[/]    [bold magenta]{anom:.2f} / 100[/]\n"
                f"[dim]Status:[/]            [bold green]INDEXED IN IN-MEMORY GRAPH & SQLITE[/]",
                title="[bold green][*] SYNTHETIC ATTACK MODEL INGESTED LIVE[/bold green]",
                border_style="green",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        return

    # Case 2: Raw JSON string
    raw_str = " ".join(args).strip()
    try:
        payload = json.loads(raw_str)
    except json.JSONDecodeError as e:
        error_panel("Invalid JSON Payload", f"Could not parse JSON: {e}")
        return

    data = client.ingest_transaction(payload)
    if not data:
        return

    txid = data.get("transaction", {}).get("txid", "-")
    risk = data.get("risk_assessment", {})
    typo = risk.get("predicted_typology", "UNKNOWN").upper()
    p_risk = risk.get("risk_score", 0.0) * 100
    anom = risk.get("anomaly_score", 0.0)

    console.print()
    console.print(
        Panel(
            f"[dim]Payload Status:[/]    [bold green]INGESTION SUCCESSFUL[/]\n"
            f"[dim]Assigned TxID:[/]     [bold yellow]{txid}[/]\n"
            f"[dim]XGBoost Risk:[/]      [bold red]{p_risk:.1f}%[/]   "
            f"[dim]Typology:[/]   [bold yellow]{typo}[/]\n"
            f"[dim]Anomaly Rating:[/]    [bold magenta]{anom:.2f} / 100[/]",
            title="[bold green][*] CUSTOM TRANSACTION INGESTED & SCORED[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
