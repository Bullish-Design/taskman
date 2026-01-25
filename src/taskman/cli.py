"""TaskMan CLI - main command-line interface."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from taskman.config import get_config, set_config, TaskManConfig
from taskman.executor import execute_commands, preview_changes
from taskman.export import export_single_task, export_tasks, TaskExportError
from taskman.llm import analyze_task, batch_analyze, revise_task
from taskman.parser import parse_revise_script, ParseError
from taskman.policy import get_policy, Policy
from taskman.uda import build_uda_registry, get_uda_names, sync_udas
from taskman.validator import validate_commands, ValidationError

app = typer.Typer(
    help="TaskMan: Orchestration + safety layer for Taskwarrior with LLM integration",
    no_args_is_help=True,
)
console = Console()


@app.command()
def sync_udas_cmd(
    model_paths: list[str] = typer.Option(
        [],
        "--model",
        "-m",
        help="Python module paths for UDA discovery",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for UDA config (default: ~/.taskrc-udas)",
    ),
) -> None:
    """Sync Taskdantic-defined UDAs into taskrc configuration.

    This command discovers UDA definitions from Python models and generates
    a taskrc configuration file that can be included in your main taskrc.
    """
    console.print("[bold blue]TaskMan UDA Sync[/bold blue]\n")

    try:
        config = get_config()
        paths = model_paths or config.uda_models_modules

        if not paths:
            console.print(
                "[red]Error:[/red] No model paths specified. "
                "Use --model or set TASKMAN_UDA_MODELS_MODULES",
                file=sys.stderr,
            )
            raise typer.Exit(1)

        console.print(f"Discovering UDAs from: {', '.join(paths)}")
        registry = build_uda_registry(paths)

        console.print(f"Found {len(get_uda_names(registry))} UDAs")

        # Sync to file
        out_path = output or get_config().uda_config_file
        sync_udas(registry, out_path=out_path)

        console.print(f"\n[green]✓[/green] UDA configuration written to: {out_path}")
        console.print(f"\nEnsure your taskrc includes this file:")
        console.print(f"  [cyan]include {out_path}[/cyan]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        raise typer.Exit(1)


@app.command()
def analyze(
    selector: str = typer.Argument(..., help="Task selector (id, uuid, or filter)"),
    mode: str = typer.Option("safe", "--mode", "-m", help="Policy mode: safe or power"),
    show_prompt: bool = typer.Option(False, "--show-prompt", help="Show LLM prompt"),
) -> None:
    """Analyze a task using LLM.

    Provides insights, suggestions, and identifies missing context.
    """
    console.print("[bold blue]TaskMan Analyze[/bold blue]\n")

    try:
        # Load configuration
        config = get_config()
        if show_prompt:
            config.show_prompt = True

        # Get policy and registry
        policy = get_policy(mode)
        registry = _load_uda_registry(config)

        # Export task
        console.print(f"Exporting task: {selector}")
        task = export_single_task(selector)

        console.print(f"Task: {task.description}")
        console.print(f"UUID: {task.uuid}\n")

        # Analyze
        console.print("Analyzing task with LLM...\n")
        result = analyze_task(task, registry=registry, policy=policy)

        # Display results
        console.print(Panel(result.summary, title="Summary", border_style="blue"))

        if result.insights:
            console.print("\n[bold]Insights:[/bold]")
            for insight in result.insights:
                console.print(f"  • {insight}")

        if result.suggestions:
            console.print("\n[bold]Suggestions:[/bold]")
            for suggestion in result.suggestions:
                console.print(f"  • {suggestion}")

        if result.missing_context:
            console.print("\n[bold yellow]Missing Context:[/bold yellow]")
            for item in result.missing_context:
                console.print(f"  • {item}")

        if result.next_actions:
            console.print("\n[bold green]Next Actions:[/bold green]")
            for action in result.next_actions:
                console.print(f"  • {action}")

    except TaskExportError as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        raise typer.Exit(1)


@app.command()
def revise(
    selector: str = typer.Argument(..., help="Task selector (id, uuid)"),
    mode: str = typer.Option("safe", "--mode", "-m", help="Policy mode: safe or power"),
    show_prompt: bool = typer.Option(False, "--show-prompt", help="Show LLM prompt"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Don't execute, just preview"),
    skip_editor: bool = typer.Option(
        False,
        "--skip-editor",
        help="Skip editor review (dangerous!)",
    ),
) -> None:
    """Revise a task using LLM-generated suggestions.

    This command:
    1. Exports the task
    2. Generates a revise script via LLM
    3. Opens the script in your editor for review
    4. Validates the script
    5. Shows a preview of changes
    6. Executes the changes
    """
    console.print("[bold blue]TaskMan Revise[/bold blue]\n")

    try:
        # Load configuration
        config = get_config()
        if show_prompt:
            config.show_prompt = True

        # Get policy and registry
        policy = get_policy(mode)
        registry = _load_uda_registry(config)

        # Export task
        console.print(f"Exporting task: {selector}")
        task = export_single_task(selector)
        console.print(f"Task: {task.description}")
        console.print(f"UUID: {task.uuid}\n")

        # Generate revise script
        console.print("Generating revise script with LLM...\n")
        revise_output = revise_task(task, registry=registry, policy=policy)

        console.print(Panel(revise_output.analysis, title="Analysis", border_style="blue"))
        console.print(f"\n[bold]Rationale:[/bold] {revise_output.rationale}\n")

        # Show initial script
        console.print("[bold]Generated Revise Script:[/bold]")
        console.print(
            Syntax(revise_output.revise_script, "bash", theme="monokai", line_numbers=True)
        )

        # Editor review
        script = revise_output.revise_script
        if not skip_editor:
            console.print(
                f"\n[yellow]Opening script in editor ({config.editor})...[/yellow]"
            )
            script = _edit_in_editor(revise_output.revise_script, config.editor)

        # Parse script
        console.print("\n[bold]Parsing revise script...[/bold]")
        try:
            commands = parse_revise_script(script)
            console.print(f"✓ Parsed {len(commands)} command(s)")
        except ParseError as e:
            console.print(f"[red]Parse Error:[/red] {e}", file=sys.stderr)
            raise typer.Exit(1)

        # Validate
        console.print("[bold]Validating commands...[/bold]")
        validation = validate_commands(commands, policy, get_uda_names(registry))

        if not validation.is_valid:
            console.print(f"[red]Validation Failed:[/red]\n{validation.get_error_summary()}")
            raise typer.Exit(1)

        console.print("✓ All commands valid\n")

        # Preview changes
        console.print("[bold]Preview of changes:[/bold]")
        diffs = preview_changes(validation.normalized_commands)
        for diff in diffs:
            console.print(Panel(str(diff), border_style="yellow"))

        # Confirm execution
        if not dry_run:
            if not typer.confirm("\nExecute these changes?"):
                console.print("[yellow]Aborted[/yellow]")
                raise typer.Exit(0)

            # Execute
            console.print("\n[bold]Executing commands...[/bold]")
            report = execute_commands(validation.normalized_commands, stop_on_error=True)

            console.print(f"\n{report.get_summary()}")

            if report.all_successful:
                console.print("\n[green]✓ All commands executed successfully[/green]")
            else:
                console.print("\n[red]Some commands failed[/red]")
                raise typer.Exit(1)
        else:
            console.print("\n[yellow]Dry run - no changes made[/yellow]")

    except TaskExportError as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        raise typer.Exit(1)


@app.command()
def batch_analyze_cmd(
    filter_expr: str = typer.Argument("status:pending", help="Taskwarrior filter"),
    mode: str = typer.Option("safe", "--mode", "-m", help="Policy mode"),
    show_prompt: bool = typer.Option(False, "--show-prompt", help="Show LLM prompt"),
) -> None:
    """Batch analyze multiple tasks.

    Analyzes consistency and provides systemic insights across tasks.
    """
    console.print("[bold blue]TaskMan Batch Analyze[/bold blue]\n")

    try:
        # Load configuration
        config = get_config()
        if show_prompt:
            config.show_prompt = True

        # Get policy and registry
        policy = get_policy(mode)
        registry = _load_uda_registry(config)

        # Export tasks
        console.print(f"Exporting tasks: {filter_expr}")
        tasks = export_tasks(filter_expr)
        console.print(f"Found {len(tasks)} task(s)\n")

        if not tasks:
            console.print("[yellow]No tasks to analyze[/yellow]")
            raise typer.Exit(0)

        # Batch analyze
        console.print("Analyzing tasks with LLM...\n")
        result = batch_analyze(tasks, registry=registry, policy=policy)

        # Display results
        table = Table(title="Analysis Results")
        table.add_column("Task", style="cyan")
        table.add_column("Summary")
        table.add_column("Suggestions", style="yellow")

        for analysis in result.analyses:
            task_desc = next(
                (t.description for t in tasks if t.uuid == analysis.uuid),
                "Unknown",
            )
            suggestions = "\n".join(analysis.suggestions[:3])  # Limit to 3
            table.add_row(task_desc[:50], analysis.summary[:100], suggestions[:100])

        console.print(table)

        if result.global_insights:
            console.print("\n[bold]Global Insights:[/bold]")
            for insight in result.global_insights:
                console.print(f"  • {insight}")

        if result.consistency_issues:
            console.print("\n[bold yellow]Consistency Issues:[/bold yellow]")
            for issue in result.consistency_issues:
                console.print(f"  • {issue}")

    except TaskExportError as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show TaskMan version."""
    from taskman import __version__

    console.print(f"TaskMan version {__version__}")


def _edit_in_editor(content: str, editor: str = "vim") -> str:
    """Open content in editor and return edited result.

    Args:
        content: Initial content
        editor: Editor command

    Returns:
        Edited content
    """
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".sh", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Open in editor
        subprocess.run([editor, temp_path], check=True)

        # Read edited content
        with open(temp_path) as f:
            edited = f.read()

        return edited
    finally:
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)


def _load_uda_registry(config: TaskManConfig) -> object | None:
    if config.uda_models_modules:
        return build_uda_registry(config.uda_models_modules)
    return None


if __name__ == "__main__":
    app()
