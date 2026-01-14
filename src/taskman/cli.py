# src/taskman/cli.py
from __future__ import annotations

import subprocess
import sys

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    help="TaskWarrior CLI wrapper with enhanced functionality",
    no_args_is_help=True,
)
console = Console()


@app.command()
def add(description: str, project: str | None = None, priority: str | None = None) -> None:
    """Add a new task."""
    cmd = ["task", "add", description]
    if project:
        cmd.append(f"project:{project}")
    if priority:
        cmd.append(f"priority:{priority}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        console.print(f"[green]✓[/green] Task added: {description}")
    else:
        console.print(f"[red]Error:[/red] {result.stderr}", file=sys.stderr)
        sys.exit(1)


@app.command()
def list(
    project: str | None = typer.Option(None, "--project", "-p", help="Filter by project")
) -> None:
    """List all pending tasks."""
    cmd = ["task"]
    if project:
        cmd.append(f"project:{project}")
    cmd.append("list")
    
    subprocess.run(cmd)


@app.command()
def next(
    limit: int = typer.Option(5, "--limit", "-n", help="Number of tasks to show")
) -> None:
    """Show next tasks to work on."""
    subprocess.run(["task", "next", f"limit:{limit}"])


@app.command()
def done(task_id: int) -> None:
    """Mark a task as complete."""
    result = subprocess.run(
        ["task", str(task_id), "done"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        console.print(f"[green]✓[/green] Task {task_id} completed!")
    else:
        console.print(f"[red]Error:[/red] {result.stderr}", file=sys.stderr)
        sys.exit(1)


@app.command()
def projects() -> None:
    """List all projects."""
    subprocess.run(["task", "projects"])


@app.command()
def info(task_id: int) -> None:
    """Show detailed information about a task."""
    subprocess.run(["task", str(task_id), "info"])


if __name__ == "__main__":
    app()
