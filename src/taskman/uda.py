"""UDA operations backed by Taskdantic."""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Callable

from taskdantic import uda as taskdantic_uda


def _resolve_callable(names: list[str]) -> Callable[..., Any]:
    for name in names:
        candidate = getattr(taskdantic_uda, name, None)
        if callable(candidate):
            return candidate
    raise AttributeError(
        "Taskdantic UDA API did not expose an expected helper: "
        f"{', '.join(names)}"
    )


def _call_with_paths(func: Callable[..., Any], model_paths: list[str]) -> Any:
    signature = inspect.signature(func)
    params = list(signature.parameters.values())
    if not params:
        return func()
    if len(params) == 1:
        return func(model_paths)
    kwargs: dict[str, Any] = {}
    for param in params:
        if param.name in {"model_paths", "module_paths", "modules", "paths"}:
            kwargs[param.name] = model_paths
    if kwargs:
        return func(**kwargs)
    return func(model_paths)


def _call_taskrc_writer(
    func: Callable[..., Any], registry: Any, out_path: Path
) -> Any:
    signature = inspect.signature(func)
    params = list(signature.parameters.values())
    if not params:
        return func()
    if len(params) == 1:
        return func(registry)
    if len(params) == 2:
        return func(registry, out_path)
    kwargs: dict[str, Any] = {}
    for param in params:
        if param.name in {"registry", "uda_registry", "udas"}:
            kwargs[param.name] = registry
        if param.name in {"out_path", "path", "output_path", "taskrc_path"}:
            kwargs[param.name] = out_path
    if kwargs:
        return func(**kwargs)
    return func(registry, out_path)


def build_uda_registry(model_paths: list[str]) -> Any:
    """Build a Taskdantic UDA registry from model module paths."""
    builder = _resolve_callable(
        [
            "build_uda_registry",
            "build_registry",
            "discover_uda_registry",
            "discover_registry",
            "discover_udas",
        ]
    )
    return _call_with_paths(builder, model_paths)


def write_uda_taskrc(registry: Any, out_path: Path) -> None:
    """Write a Taskdantic registry to a taskrc-compatible file."""
    writer = _resolve_callable(
        [
            "write_uda_taskrc",
            "write_taskrc",
            "write_taskrc_config",
            "export_taskrc",
            "export_taskrc_config",
            "render_taskrc_config",
        ]
    )
    result = _call_taskrc_writer(writer, registry, out_path)
    if isinstance(result, str):
        out_path.write_text(result)


def sync_udas(registry: Any, out_path: Path | None = None) -> None:
    """Sync Taskdantic UDAs to a taskrc configuration file."""
    if out_path is None:
        out_path = Path.home() / ".taskrc-udas"
    write_uda_taskrc(registry, out_path)


def get_uda_names(registry: Any) -> set[str]:
    """Extract UDA names from a Taskdantic registry."""
    if registry is None:
        return set()
    for attr in ("get_names", "names", "uda_names"):
        value = getattr(registry, attr, None)
        if callable(value):
            return set(value())
        if value:
            return set(value)
    udas = getattr(registry, "udas", None)
    if isinstance(udas, dict):
        return set(udas.keys())
    if hasattr(registry, "__iter__"):
        return {getattr(item, "name") for item in registry if hasattr(item, "name")}
    return set()


def format_uda_prompt_reference(registry: Any) -> str:
    """Render a prompt-friendly UDA reference."""
    if registry is None:
        return "No UDAs defined."
    if hasattr(registry, "to_prompt_reference"):
        return registry.to_prompt_reference()
    formatter = getattr(taskdantic_uda, "format_prompt_reference", None)
    if callable(formatter):
        return formatter(registry)
    names = sorted(get_uda_names(registry))
    if not names:
        return "No UDAs defined."
    lines = ["Available User Defined Attributes:", ""]
    lines.extend(f"- {name}" for name in names)
    return "\n".join(lines)
