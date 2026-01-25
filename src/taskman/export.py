"""Task export and selector resolution utilities."""

from __future__ import annotations

import json
import subprocess
from typing import Any, TYPE_CHECKING

from taskdantic.models import Task as TDTask

from taskman.config import get_config

if TYPE_CHECKING:
    from taskdantic import Task as TaskdanticTask
else:
    TaskdanticTask = Any


class TaskExportError(Exception):
    """Error during task export."""


class SelectorResolutionError(Exception):
    """Error resolving a selector to UUID."""


Task = TDTask


def parse_task(raw: dict[str, Any]) -> TDTask:
    """Parse a raw task dict into a Taskdantic Task."""
    return TDTask.model_validate(raw)


def get_task_udas(task: TDTask) -> dict[str, Any]:
    """Extract UDAs from a Taskdantic Task using known storage locations."""
    udas = getattr(task, "udas", None)
    if isinstance(udas, dict):
        return udas

    uda = getattr(task, "uda", None)
    if isinstance(uda, dict):
        return uda

    model_extra = getattr(task, "model_extra", None)
    if isinstance(model_extra, dict):
        return model_extra

    return {}


def export_tasks(filter_expr: str | None = None) -> list[TDTask]:
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

    return [parse_task(item) for item in data]


def export_single_task(selector: str) -> TDTask:
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


def task_to_prompt_format(task: TDTask) -> str:
    """Format a task for inclusion in LLM prompts.

    Args:
        task: Task to format

    Returns:
        Formatted string representation
    """
    uuid = getattr(task, "uuid", "")
    description = getattr(task, "description", "")
    project = getattr(task, "project", None)
    tags = list(getattr(task, "tags", []) or [])
    depends = list(getattr(task, "depends", []) or [])
    annotations = list(getattr(task, "annotations", []) or [])
    udas = get_task_udas(task)

    lines = [
        f"UUID: {uuid}",
        f"Description: {description}",
    ]

    if project:
        lines.append(f"Project: {project}")

    if tags:
        lines.append(f"Tags: {', '.join(tags)}")

    if depends:
        lines.append(f"Depends: {', '.join(depends)}")

    if udas:
        lines.append("\nUser Defined Attributes:")
        for key, value in sorted(udas.items()):
            lines.append(f"  {key}: {value}")

    if annotations:
        lines.append("\nAnnotations:")
        for ann in annotations:
            entry = ann.get("entry", "")
            desc = ann.get("description", "")
            lines.append(f"  [{entry}] {desc}")

    return "\n".join(lines)
