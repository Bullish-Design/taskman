"""Safe command execution for revise scripts."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from taskman.config import get_config
from taskman.export import export_single_task, get_task_udas, Task
from taskman.parser import CommandAST, command_to_string

if TYPE_CHECKING:
    from taskdantic import Task as TaskdanticTask
else:
    TaskdanticTask = Any


class ExecutionError(Exception):
    """Error during command execution."""


@dataclass
class CommandResult:
    """Result of executing a single command."""

    command: CommandAST
    success: bool
    output: str = ""
    error: str = ""

    @property
    def command_string(self) -> str:
        """Get string representation of command."""
        return command_to_string(self.command)


@dataclass
class ExecutionReport:
    """Report of execution results."""

    total_commands: int = 0
    successful: int = 0
    failed: int = 0
    results: list[CommandResult] = field(default_factory=list)

    def add_result(self, result: CommandResult) -> None:
        """Add a command result."""
        self.results.append(result)
        self.total_commands += 1
        if result.success:
            self.successful += 1
        else:
            self.failed += 1

    @property
    def all_successful(self) -> bool:
        """Check if all commands succeeded."""
        return self.failed == 0 and self.total_commands > 0

    def get_summary(self) -> str:
        """Get execution summary."""
        if self.total_commands == 0:
            return "No commands executed"

        lines = [
            f"Execution Summary:",
            f"  Total commands: {self.total_commands}",
            f"  Successful: {self.successful}",
            f"  Failed: {self.failed}",
        ]

        if self.failed > 0:
            lines.append("\nFailed commands:")
            for result in self.results:
                if not result.success:
                    lines.append(f"  - {result.command_string}")
                    if result.error:
                        lines.append(f"    Error: {result.error}")

        return "\n".join(lines)


@dataclass
class DiffEntry:
    """A single diff entry for a field change."""

    field: str
    before: Any
    after: Any

    def __str__(self) -> str:
        """String representation."""
        return f"{self.field}: {self.before} → {self.after}"


@dataclass
class TaskDiff:
    """Diff for a single task."""

    uuid: str
    changes: list[DiffEntry] = field(default_factory=list)

    def add_change(self, field: str, before: Any, after: Any) -> None:
        """Add a field change."""
        self.changes.append(DiffEntry(field=field, before=before, after=after))

    def __str__(self) -> str:
        """String representation."""
        if not self.changes:
            return f"Task {self.uuid[:8]}: No changes"

        lines = [f"Task {self.uuid[:8]}:"]
        for change in self.changes:
            lines.append(f"  {change}")
        return "\n".join(lines)


class CommandExecutor:
    """Executor for validated revise script commands."""

    def __init__(self, stop_on_error: bool = True, dry_run: bool = False):
        """Initialize executor.

        Args:
            stop_on_error: Stop execution on first error
            dry_run: Don't actually execute, just simulate
        """
        self.stop_on_error = stop_on_error
        self.dry_run = dry_run
        self.config = get_config()

    def execute(self, commands: list[CommandAST]) -> ExecutionReport:
        """Execute a list of validated commands.

        Args:
            commands: List of validated CommandAST nodes

        Returns:
            ExecutionReport with results

        Raises:
            ExecutionError: If execution fails and stop_on_error is True
        """
        report = ExecutionReport()

        for cmd in commands:
            result = self._execute_command(cmd)
            report.add_result(result)

            if not result.success and self.stop_on_error:
                raise ExecutionError(
                    f"Command failed: {result.command_string}\n"
                    f"Error: {result.error}\n"
                    f"Stopping execution due to error."
                )

        return report

    def _execute_command(self, cmd: CommandAST) -> CommandResult:
        """Execute a single command.

        Args:
            cmd: Command to execute

        Returns:
            CommandResult
        """
        # Build taskwarrior command
        tw_cmd = self._build_taskwarrior_command(cmd)

        if self.dry_run:
            return CommandResult(
                command=cmd,
                success=True,
                output=f"[DRY RUN] Would execute: {' '.join(tw_cmd)}",
            )

        # Execute
        try:
            result = subprocess.run(
                tw_cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            return CommandResult(
                command=cmd,
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
            )
        except Exception as e:
            return CommandResult(
                command=cmd,
                success=False,
                error=str(e),
            )

    def _build_taskwarrior_command(self, cmd: CommandAST) -> list[str]:
        """Build taskwarrior command from AST.

        Args:
            cmd: Command AST

        Returns:
            List of command arguments
        """
        tw_cmd = [self.config.task_bin, cmd.selector]

        if cmd.is_modify and cmd.operations:
            tw_cmd.append("modify")
            for op in cmd.operations:
                if op.operation == "add":
                    tw_cmd.append(f"+{op.value}")
                elif op.operation == "remove":
                    tw_cmd.append(f"-{op.value}")
                elif op.operation == "set" and op.value is not None:
                    tw_cmd.append(f"{op.field}:{op.value}")

        elif cmd.is_annotate and cmd.annotation_text:
            tw_cmd.append("annotate")
            tw_cmd.append(cmd.annotation_text)

        return tw_cmd

    def preview_changes(self, commands: list[CommandAST]) -> list[TaskDiff]:
        """Preview what changes commands will make.

        Args:
            commands: List of validated commands

        Returns:
            List of TaskDiff objects
        """
        diffs: dict[str, TaskDiff] = {}

        for cmd in commands:
            uuid = cmd.selector

            # Get or create diff for this task
            if uuid not in diffs:
                diffs[uuid] = TaskDiff(uuid=uuid)

            task_diff = diffs[uuid]

            # Compute changes based on command
            if cmd.is_modify and cmd.operations:
                # Get current task state
                try:
                    task = export_single_task(uuid)
                except Exception:
                    # If we can't export, skip preview for this task
                    continue

                for op in cmd.operations:
                    self._compute_field_diff(task, op.field, op.operation, op.value, task_diff)

            elif cmd.is_annotate and cmd.annotation_text:
                task_diff.add_change(
                    "annotations",
                    "[current]",
                    f"+ {cmd.annotation_text}",
                )

        return list(diffs.values())

    def _compute_field_diff(
        self,
        task: TaskdanticTask,
        field: str,
        operation: str,
        value: Any,
        diff: TaskDiff,
    ) -> None:
        """Compute diff for a field operation.

        Args:
            task: Current task state
            field: Field name
            operation: Operation type (set, add, remove)
            value: Operation value
            diff: TaskDiff to update
        """
        if field == "tags":
            current = set(task.tags)
            if operation == "add":
                after = current | {value}
                diff.add_change("tags", list(current), list(after))
            elif operation == "remove":
                after = current - {value}
                diff.add_change("tags", list(current), list(after))
        else:
            # For other fields, show before/after
            current = getattr(task, field, None)
            if current is None:
                current = get_task_udas(task).get(field)

            if operation == "set":
                diff.add_change(field, current, value)


def execute_commands(
    commands: list[CommandAST],
    stop_on_error: bool = True,
    dry_run: bool = False,
) -> ExecutionReport:
    """Execute a list of validated commands.

    Args:
        commands: List of validated CommandAST nodes
        stop_on_error: Stop execution on first error
        dry_run: Don't actually execute, just simulate

    Returns:
        ExecutionReport with results

    Raises:
        ExecutionError: If execution fails and stop_on_error is True
    """
    executor = CommandExecutor(stop_on_error=stop_on_error, dry_run=dry_run)
    return executor.execute(commands)


def preview_changes(commands: list[CommandAST]) -> list[TaskDiff]:
    """Preview what changes commands will make.

    Args:
        commands: List of validated commands

    Returns:
        List of TaskDiff objects
    """
    executor = CommandExecutor()
    return executor.preview_changes(commands)
