"""Task export and selector resolution utilities."""

from __future__ import annotations

import json
import subprocess
from typing import Any, TYPE_CHECKING

from pydantic import BaseModel

from taskman.config import get_config

if TYPE_CHECKING:
    from taskdantic import Task as TaskdanticTask
else:
    TaskdanticTask = Any


class TaskExportError(Exception):
    """Error during task export."""


class SelectorResolutionError(Exception):
    """Error resolving a selector to UUID."""


class Task(BaseModel):
    """Simplified task model for TaskMan operations.

    This is a lightweight model for tasks exported from Taskwarrior.
    For full Taskdantic integration, we'll use their models where appropriate.
    """

    id: int | None = None
    uuid: str
    description: str
    status: str
    entry: str
    modified: str | None = None
    project: str | None = None
    tags: list[str] = []
    priority: str | None = None
    due: str | None = None
    until: str | None = None
    wait: str | None = None
    scheduled: str | None = None
    depends: list[str] = []
    annotations: list[dict[str, Any]] = []
    urgency: float = 0.0

    # Store any additional fields (including UDAs)
    uda: dict[str, Any] = {}

    class Config:
        extra = "allow"  # Allow extra fields for UDAs

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization to capture UDAs."""
        # Capture any extra fields as UDAs
        known_fields = {
            "id",
            "uuid",
            "description",
            "status",
            "entry",
            "modified",
            "project",
            "tags",
            "priority",
            "due",
            "until",
            "wait",
            "scheduled",
            "depends",
            "annotations",
            "urgency",
            "uda",
        }
        for field_name in dir(self):
            if not field_name.startswith("_") and field_name not in known_fields:
                value = getattr(self, field_name, None)
                if value is not None:
                    self.uda[field_name] = value


def export_tasks(filter_expr: str | None = None) -> list[Task]:
    """Export tasks from Taskwarrior.

    Args:
        filter_expr: Optional Taskwarrior filter expression (e.g., "status:pending")

    Returns:
        List of Task objects

    Raises:
        TaskExportError: If export fails
    """
    config = get_config()
    cmd = [config.task_bin, "export"]

    if filter_expr:
        # Insert filter before 'export'
        cmd = [config.task_bin] + filter_expr.split() + ["export"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise TaskExportError(f"Failed to export tasks: {e.stderr}") from e

    if not result.stdout.strip():
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise TaskExportError(f"Failed to parse task JSON: {e}") from e

    tasks = []
    for item in data:
        # Handle UDA fields by extracting known vs unknown
        task_dict = {k: v for k, v in item.items()}
        tasks.append(Task(**task_dict))

    return tasks


def export_single_task(selector: str) -> Task:
    """Export a single task by selector.

    Args:
        selector: Task selector (id, uuid, or filter)

    Returns:
        Single Task object

    Raises:
        TaskExportError: If export fails or doesn't return exactly one task
    """
    tasks = export_tasks(selector)

    if len(tasks) == 0:
        raise TaskExportError(f"No task found matching selector: {selector}")
    if len(tasks) > 1:
        raise TaskExportError(
            f"Selector '{selector}' matched {len(tasks)} tasks. "
            f"Please provide a more specific selector."
        )

    return tasks[0]


def resolve_selector(selector: str) -> str:
    """Resolve a selector to a UUID.

    This function takes a user-friendly selector (like a numeric ID)
    and resolves it to the corresponding task UUID for unambiguous
    internal operations.

    Args:
        selector: Task selector (id, uuid, or other taskwarrior selector)

    Returns:
        Task UUID

    Raises:
        SelectorResolutionError: If selector cannot be resolved
    """
    # If it already looks like a UUID, return it
    if len(selector) == 36 and selector.count("-") == 4:
        return selector

    # Otherwise, export the task and get its UUID
    try:
        task = export_single_task(selector)
        return task.uuid
    except TaskExportError as e:
        raise SelectorResolutionError(f"Failed to resolve selector '{selector}': {e}") from e


def resolve_selectors(selectors: list[str]) -> list[str]:
    """Resolve multiple selectors to UUIDs.

    Args:
        selectors: List of task selectors

    Returns:
        List of resolved UUIDs

    Raises:
        SelectorResolutionError: If any selector cannot be resolved
    """
    return [resolve_selector(s) for s in selectors]


def normalize_depends(depends: list[str] | str) -> list[str]:
    """Normalize depends field to list of UUIDs.

    Args:
        depends: Depends value (can be comma-separated string or list)

    Returns:
        List of UUIDs

    Raises:
        SelectorResolutionError: If any dependency cannot be resolved
    """
    if isinstance(depends, str):
        if not depends:
            return []
        dep_list = [d.strip() for d in depends.split(",")]
    else:
        dep_list = depends

    # Resolve each dependency to UUID
    return resolve_selectors(dep_list)


def task_to_prompt_format(task: Task | TaskdanticTask) -> str:
    """Format a task for inclusion in LLM prompts.

    Args:
        task: Task to format

    Returns:
        Formatted string representation
    """
    lines = [
        f"UUID: {task.uuid}",
        f"Description: {task.description}",
        f"Status: {task.status}",
    ]

    if task.project:
        lines.append(f"Project: {task.project}")

    if task.tags:
        lines.append(f"Tags: {', '.join(task.tags)}")

    if task.priority:
        lines.append(f"Priority: {task.priority}")

    if task.due:
        lines.append(f"Due: {task.due}")

    if task.wait:
        lines.append(f"Wait: {task.wait}")

    if task.scheduled:
        lines.append(f"Scheduled: {task.scheduled}")

    if task.depends:
        lines.append(f"Depends: {', '.join(task.depends)}")

    # Add UDAs
    if task.uda:
        lines.append("\nUser Defined Attributes:")
        for key, value in sorted(task.uda.items()):
            lines.append(f"  {key}: {value}")

    # Add annotations
    if task.annotations:
        lines.append("\nAnnotations:")
        for ann in task.annotations:
            entry = ann.get("entry", "")
            desc = ann.get("description", "")
            lines.append(f"  [{entry}] {desc}")

    return "\n".join(lines)
