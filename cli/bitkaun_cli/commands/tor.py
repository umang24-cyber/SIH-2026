"""
Tor command for BitKaun CLI.
Profiles transaction Shannon timing entropy and evasion score against Tor exit node infrastructure.
"""

from rich.panel import Panel
from rich.table import Table
from rich import box
from ..api_client import client
from ..render import console, warning_panel


def execute(args: list[str] = None):
    """Execute the tor command."""
    if not args:
        summary = client.get_tor_summary()
        if not summary:
            return

        total_tx = summary.get("total_tor_transactions", 0)
        exits = summary.get("active_exit_nodes", 0)
        entropy = summary.get("mean_timing_entropy", 0.0)

        console.print()
        console.print(
            Panel(
                f"[dim]Total Tor Transactions:[/] [bold red]{total_tx:,}[/]\n"
                f"[dim]Known Tor Exit Nodes:[/]   [bold yellow]{exits:,}[/]\n"
                f"[dim]Mean Timing Entropy:[/]    [bold cyan]{entropy:.4f}[/]",
                title="[bold yellow][*] TOR ON-CHAIN & NETWORK INFRASTRUCTURE INTELLIGENCE[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        return

    txid = args[0].strip()
    data = client.get_tor_profiler(txid)
    if not data:
        return

    is_tor = data.get("is_tor_relay", False)
    entropy = data.get("shannon_timing_entropy", 0.0)
    evasion = data.get("obfuscation_evasion_score", 0.0)
    ip = data.get("relay_ip", "-")
    asn = data.get("asn", "-")

    console.print()
    console.print(
        Panel(
            f"[dim]Target TxID:[/]          [bold cyan]{txid}[/]\n"
            f"[dim]Relay IP Address:[/]     [bold yellow]{ip}[/]  [dim]ASN:[/] [white]{asn}[/]\n"
            f"[dim]Tor Exit Detected:[/]    [{'bold red' if is_tor else 'green'}]{'YES [CONFIRMED TOR NODE]' if is_tor else 'NO [CLEARNET / RESIDENTIAL]'}[/]\n"
            f"[dim]Timing Entropy:[/]       [bold cyan]{entropy:.4f}[/]  [dim](0 = perfectly automated / scripted)[/]\n"
            f"[dim]Evasion Score:[/]        [bold magenta]{evasion:.2f} / 1.0[/]",
            title="[bold red][*] TOR INFRASTRUCTURE & TIMING ENTROPY PROFILER[/bold red]",
            border_style="red" if is_tor else "green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
    console.print()
