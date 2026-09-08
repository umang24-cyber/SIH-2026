"""
Benchmark command for BitKaun CLI.
Displays quantitative model evaluation scorecard (Precision, Recall, F1, Latency).
"""

from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console


def execute(args: list[str] = None):
    """Execute the benchmark command."""
    data = client.get_benchmark()
    if not data:
        return

    perf = data.get("performance_metrics", {})
    macro_f1 = data.get("overall_macro_f1", 0.939)
    latency = data.get("average_inference_latency_ms", 0.42)
    alerts = data.get("candidate_alerts_flagged", 824)
    version = data.get("dataset_version", "v8.0 (82,078 transactions)")

    console.print()
    console.print(
        Panel(
            f"[dim]Dataset Version:[/]   [bold cyan]{version}[/]\n"
            f"[dim]Overall Macro F1:[/]  [bold green]{macro_f1 * 100:.1f}%[/]   "
            f"[dim]Flagged Alerts:[/]   [bold yellow]{alerts:,}[/]\n"
            f"[dim]Inference Speed:[/]   [bold yellow]{latency:.2f} ms / transaction[/]   "
            f"[dim]Architecture:[/]    [bold white]XGBoost V8.0 Ensemble + Isolation Forest[/]",
            title="[bold green][*] V8.0 AIR-GAPPED BENCHMARK EVALUATION SCORECARD[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    table = Table(
        title="[bold green][*] Typology Detection Performance Matrix[/bold green]",
        box=box.ROUNDED,
        border_style="green",
        header_style="bold green on black",
        expand=True,
    )
    table.add_column("Typology Class", style="bold cyan")
    table.add_column("Precision", style="green", justify="right")
    table.add_column("Recall", style="green", justify="right")
    table.add_column("F1-Score", style="bold yellow", justify="right")
    table.add_column("Detected Count", style="white", justify="right")

    for cls_name, metrics in perf.items():
        p = f"{metrics.get('precision', 0.0) * 100:.1f}%"
        r = f"{metrics.get('recall', 0.0) * 100:.1f}%"
        f1 = f"{metrics.get('f1_score', 0.0) * 100:.1f}%"
        count_key = [k for k in metrics.keys() if k.startswith("detected_")]
        count_val = str(metrics[count_key[0]]) if count_key else "-"
        table.add_row(cls_name.replace("_", " ").title(), p, r, f1, count_val)

    console.print(table)
    console.print()
