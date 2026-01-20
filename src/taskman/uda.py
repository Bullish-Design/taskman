"""UDA operations - wrapper around Taskdantic functionality."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel


class UDASpec(BaseModel):
    """Specification for a User Defined Attribute.

    This is a simplified version for TaskMan's needs.
    The actual implementation will use Taskdantic's UDA models.
    """

    name: str
    type: str  # string, numeric, date, duration
    label: str | None = None
    values: list[str] | None = None  # For enumerated types
    default: str | None = None
    urgent: float | None = None
    help: str | None = None


class UDARegistry:
    """Registry of User Defined Attributes.

    This wraps Taskdantic's UDA registry functionality.
    """

    def __init__(self) -> None:
        """Initialize registry."""
        self.udas: dict[str, UDASpec] = {}

    def register(self, uda: UDASpec) -> None:
        """Register a UDA.

        Args:
            uda: UDA specification
        """
        self.udas[uda.name] = uda

    def get(self, name: str) -> UDASpec | None:
        """Get a UDA by name.

        Args:
            name: UDA name

        Returns:
            UDA spec or None
        """
        return self.udas.get(name)

    def get_names(self) -> set[str]:
        """Get all UDA names.

        Returns:
            Set of UDA names
        """
        return set(self.udas.keys())

    def to_taskrc_config(self) -> str:
        """Generate taskrc configuration for all UDAs.

        Returns:
            Taskrc configuration block
        """
        lines = ["# User Defined Attributes (managed by TaskMan)", ""]

        for name, uda in sorted(self.udas.items()):
            # Type
            lines.append(f"uda.{name}.type={uda.type}")

            # Label
            if uda.label:
                lines.append(f"uda.{name}.label={uda.label}")

            # Values (for enumerated types)
            if uda.values:
                lines.append(f"uda.{name}.values={','.join(uda.values)}")

            # Default
            if uda.default:
                lines.append(f"uda.{name}.default={uda.default}")

            # Urgency
            if uda.urgent is not None:
                lines.append(f"urgency.uda.{name}.coefficient={uda.urgent}")

            lines.append("")  # Blank line between UDAs

        return "\n".join(lines)

    def to_prompt_reference(self) -> str:
        """Generate a prompt-friendly reference of all UDAs.

        Returns:
            Human-readable UDA reference
        """
        if not self.udas:
            return "No UDAs defined."

        lines = ["Available User Defined Attributes:", ""]

        for name, uda in sorted(self.udas.items()):
            desc = f"- {name} ({uda.type})"
            if uda.label:
                desc += f" - {uda.label}"
            lines.append(desc)

            if uda.help:
                lines.append(f"  {uda.help}")

            if uda.values:
                lines.append(f"  Allowed values: {', '.join(uda.values)}")

            if uda.default:
                lines.append(f"  Default: {uda.default}")

            lines.append("")

        return "\n".join(lines)

    @classmethod
    def from_models(cls, model_paths: list[str]) -> UDARegistry:
        """Build a UDA registry from Taskdantic model modules.

        Args:
            model_paths: List of Python module paths

        Returns:
            UDARegistry instance

        Note:
            This is a placeholder. The actual implementation will use
            Taskdantic's UDA discovery and registry functionality.
        """
        registry = cls()

        # TODO: Integrate with Taskdantic's UDA discovery
        # For now, return empty registry
        # The actual implementation will:
        # 1. Import modules from model_paths
        # 2. Use Taskdantic's UDA discovery to find UDA models
        # 3. Convert to UDASpec and register

        return registry


def build_uda_registry(model_paths: list[str]) -> UDARegistry:
    """Build a UDA registry from model paths.

    Args:
        model_paths: List of Python module paths to discover UDAs from

    Returns:
        UDARegistry instance
    """
    return UDARegistry.from_models(model_paths)


def sync_udas(
    registry: UDARegistry,
    taskrc_path: Path | None = None,
    out_path: Path | None = None,
) -> None:
    """Sync UDAs to taskrc configuration.

    Args:
        registry: UDA registry
        taskrc_path: Path to main taskrc (for reference)
        out_path: Path to write UDA config (defaults to ~/.taskrc-udas)

    Note:
        This writes to a separate file that should be included in taskrc:
        include ~/.taskrc-udas
    """
    if out_path is None:
        out_path = Path.home() / ".taskrc-udas"

    # Generate config
    config = registry.to_taskrc_config()

    # Write to file
    out_path.write_text(config)
    print(f"UDA configuration written to: {out_path}")
    print(f"\nEnsure your taskrc includes this file:")
    print(f"  include {out_path}")


def create_example_registry() -> UDARegistry:
    """Create an example UDA registry for testing/demonstration.

    Returns:
        UDARegistry with example UDAs
    """
    registry = UDARegistry()

    # Example UDAs from the spec
    registry.register(
        UDASpec(
            name="context",
            type="string",
            label="Context",
            help="The context or location where this task should be done",
        )
    )

    registry.register(
        UDASpec(
            name="why",
            type="string",
            label="Why",
            help="The reason or motivation for this task",
        )
    )

    registry.register(
        UDASpec(
            name="stakeholder",
            type="string",
            label="Stakeholder",
            help="Who cares about or benefits from this task",
        )
    )

    registry.register(
        UDASpec(
            name="waiting_on",
            type="string",
            label="Waiting On",
            help="What or who this task is blocked by",
        )
    )

    registry.register(
        UDASpec(
            name="next_action",
            type="string",
            label="Next Action",
            help="The very next physical action to move this forward",
        )
    )

    registry.register(
        UDASpec(
            name="impact",
            type="string",
            label="Impact",
            values=["low", "medium", "high", "critical"],
            help="Expected impact of completing this task",
        )
    )

    registry.register(
        UDASpec(
            name="effort",
            type="string",
            label="Effort",
            values=["trivial", "small", "medium", "large", "huge"],
            help="Estimated effort required",
        )
    )

    return registry
