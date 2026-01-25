"""TaskMan: Orchestration + safety layer for Taskwarrior with LLM integration."""

from __future__ import annotations

__version__ = "0.2.0"

# Public API exports
from taskman.config import TaskManConfig, get_config, set_config
from taskman.executor import execute_commands, preview_changes, ExecutionReport
from taskman.export import (
    export_tasks,
    export_single_task,
    resolve_selector,
    resolve_selectors,
    Task,
)
from taskman.llm import analyze_task, batch_analyze, revise_task
from taskman.parser import parse_revise_script, CommandAST
from taskman.policy import Policy, PolicyMode, get_policy
from taskman.uda import (
    build_uda_registry,
    format_uda_prompt_reference,
    get_uda_names,
    sync_udas,
    write_uda_taskrc,
)
from taskman.validator import validate_commands, ValidationResult

__all__ = [
    "__version__",
    # Config
    "TaskManConfig",
    "get_config",
    "set_config",
    # Export
    "export_tasks",
    "export_single_task",
    "resolve_selector",
    "resolve_selectors",
    "Task",
    # Parser
    "parse_revise_script",
    "CommandAST",
    # Validator
    "validate_commands",
    "ValidationResult",
    # Executor
    "execute_commands",
    "preview_changes",
    "ExecutionReport",
    # Policy
    "Policy",
    "PolicyMode",
    "get_policy",
    # UDA
    "build_uda_registry",
    "format_uda_prompt_reference",
    "get_uda_names",
    "sync_udas",
    "write_uda_taskrc",
    # LLM
    "analyze_task",
    "batch_analyze",
    "revise_task",
]
