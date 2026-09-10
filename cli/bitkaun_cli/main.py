"""
Main entry point and REPL session loop for BitKaun CLI.
"""

import sys
import os
import shlex
from .render import console, print_banner, error_panel
from .commands import help_cmd

# Try importing prompt_toolkit for full arrow-key history support
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False


def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def dispatch_command(cmd_line: str) -> bool:
    """
    Parse and dispatch a single line of input to the appropriate command handler.
    Returns False if the REPL session should exit, True otherwise.
    """
    cmd_line = cmd_line.strip()
    if not cmd_line:
        return True

    try:
        parts = shlex.split(cmd_line)
    except ValueError as e:
        error_panel("Command Parse Error", str(e))
        return True

    command = parts[0].lower()
    args = parts[1:]

    # Handle redundant 'bitkaun' prefix when typed inside interactive REPL
    if command == "bitkaun":
        if args:
            command = args[0].lower()
            args = args[1:]
        else:
            print_banner()
            return True

    if command in ("exit", "quit", "q"):
        console.print("[bold green]Session terminated. Exiting BitKaun forensics terminal.[/bold green]")
        return False

    if command in ("clear", "cls"):
        clear_screen()
        print_banner()
        return True

    if command in ("help", "?"):
        help_cmd.execute(args)
        return True

    # Case management commands (Git mental model)
    if command == "init":
        from .commands import init_case
        init_case.execute(args)
        return True

    if command in ("cd", "case", "cases", "checkout", "use"):
        from .commands import cd_cmd
        cd_cmd.execute(command, args)
        return True

    if command in ("ls", "list"):
        from .commands import ls_cmd
        ls_cmd.execute(args)
        return True

    # Lazy-loaded backend commands
    if command in ("status", "sys", "health"):
        from .commands import status
        status.execute(args)
        return True

    if command == "inspect":
        from .commands import inspect
        inspect.execute(args)
        return True

    if command == "graph":
        from .commands import graph
        graph.execute(args)
        return True

    if command == "trace":
        from .commands import trace
        trace.execute(args)
        return True

    if command == "alerts":
        from .commands import alerts
        alerts.execute(args)
        return True

    if command in ("correlate", "upload"):
        from .commands import correlate
        correlate.execute(args)
        return True

    if command == "taint":
        from .commands import taint
        taint.execute(args)
        return True

    if command == "flow":
        from .commands import flow
        flow.execute(args)
        return True

    if command == "communities":
        from .commands import communities
        communities.execute(args)
        return True

    if command == "anomaly":
        from .commands import anomaly
        anomaly.execute(args)
        return True

    if command in ("search", "find", "query"):
        from .commands import search
        search.execute(args)
        return True

    if command in ("scenarios", "clusters"):
        from .commands import scenarios
        scenarios.execute(args)
        return True

    if command in ("benchmark", "eval", "metrics"):
        from .commands import benchmark
        benchmark.execute(args)
        return True

    if command in ("telemetry", "stats"):
        from .commands import telemetry
        telemetry.execute(args)
        return True

    if command == "dossier":
        from .commands import dossier
        dossier.execute(args)
        return True

    if command == "tor":
        from .commands import tor
        tor.execute(args)
        return True

    if command == "ingest":
        from .commands import ingest
        ingest.execute(args)
        return True

    if command in ("logs", "log", "stream"):
        from .commands import logs
        logs.execute(args)
        return True

    error_panel(
        "Unknown Command",
        f"'{command}' is not a recognized BitKaun command. Type [bold green]help[/bold green] for reference."
    )
    return True


def run():
    """CLI console script entry point."""
    args = sys.argv[1:]

    # Direct execution mode: e.g. `bitkaun status` or `bitkaun --help`
    if args:
        if args[0] in ("-h", "--help"):
            help_cmd.execute([])
            sys.exit(0)
        if args[0] in ("-v", "--version"):
            from . import __version__
            console.print(f"[bold green]bitkaun version {__version__}[/bold green]")
            sys.exit(0)

        cmd_string = " ".join(args)
        dispatch_command(cmd_string)
        sys.exit(0)

    # Interactive REPL mode
    if sys.stdin.isatty():
        clear_screen()
    print_banner()

    session = None
    if HAS_PROMPT_TOOLKIT and sys.stdin.isatty():
        session = PromptSession(history=InMemoryHistory())

    from .case_context import find_active_case

    while True:
        try:
            active_info = find_active_case()
            if active_info and active_info.get("case_name"):
                prompt_str = f"bitkaun@investigation ({active_info['case_name']}):~$ "
            else:
                prompt_str = "bitkaun@investigation:~$ "

            if session and sys.stdin.isatty():
                line = session.prompt(prompt_str)
            elif sys.stdin.isatty():
                line = input(prompt_str)
            else:
                line = sys.stdin.readline()
                if not line:
                    break

            should_continue = dispatch_command(line)
            if not should_continue:
                break
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold green]Session interrupted. Exiting.[/bold green]")
            break
        except Exception as e:
            error_panel("Execution Exception", str(e))


if __name__ == "__main__":
    run()

