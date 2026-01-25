"""Tests for Taskdantic UDA discovery and sync CLI."""

from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from pathlib import Path

from typer.testing import CliRunner


def _install_taskdantic_stub() -> None:
    stub = types.ModuleType("taskdantic")
    uda = types.ModuleType("taskdantic.uda")

    class TaskModel:
        """Minimal Taskdantic-like base class for model discovery."""

    @dataclass(frozen=True)
    class Uda:
        name: str
        type: str = "string"
        label: str = ""

    class UdaRegistry:
        def __init__(self, udas: dict[str, Uda]) -> None:
            self.udas = udas

        def get_names(self) -> list[str]:
            return list(self.udas.keys())

    def build_uda_registry(model_paths: list[str]) -> UdaRegistry:
        udas: dict[str, Uda] = {}
        for module_path in model_paths:
            module = importlib.import_module(module_path)
            for value in module.__dict__.values():
                if not isinstance(value, type):
                    continue
                if value is TaskModel:
                    continue
                if not issubclass(value, TaskModel):
                    continue
                for uda_def in getattr(value, "__udas__", []):
                    udas[uda_def.name] = uda_def
        return UdaRegistry(udas)

    def write_uda_taskrc(registry: UdaRegistry, out_path: Path) -> str:
        lines: list[str] = []
        for name, uda_def in registry.udas.items():
            lines.append(f"uda.{name}.type={uda_def.type}")
            if uda_def.label:
                lines.append(f"uda.{name}.label={uda_def.label}")
        return "\n".join(lines) + ("\n" if lines else "")

    uda.build_uda_registry = build_uda_registry
    uda.write_uda_taskrc = write_uda_taskrc

    stub.TaskModel = TaskModel
    stub.Uda = Uda
    stub.uda = uda

    sys.modules["taskdantic"] = stub
    sys.modules["taskdantic.uda"] = uda


def _reload_taskman_module(module_name: str) -> types.ModuleType:
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def test_build_uda_registry_discovers_taskdantic_models() -> None:
    _install_taskdantic_stub()
    uda_module = _reload_taskman_module("taskman.uda")

    registry = uda_module.build_uda_registry(["tests.fixtures.uda_models"])

    assert uda_module.get_uda_names(registry) == {"context", "effort"}


def test_sync_udas_command_writes_taskrc(tmp_path: Path) -> None:
    _install_taskdantic_stub()
    _reload_taskman_module("taskman.uda")
    cli_module = _reload_taskman_module("taskman.cli")

    output_path = tmp_path / "taskrc-udas"
    runner = CliRunner()

    result = runner.invoke(
        cli_module.app,
        [
            "sync-udas",
            "--model",
            "tests.fixtures.uda_models",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.read_text().strip()
