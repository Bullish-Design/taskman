"""Minimal Taskdantic-like models for UDA discovery tests."""

from __future__ import annotations

from taskdantic import TaskModel, Uda


class DemoTask(TaskModel):
    """Task model with a couple of UDAs for discovery tests."""

    __udas__ = [
        Uda(name="context", type="string", label="Context"),
        Uda(name="effort", type="numeric", label="Effort"),
    ]
