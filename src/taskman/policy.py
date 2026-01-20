"""Safety policy and allowlist management for TaskMan."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PolicyMode(str, Enum):
    """Policy enforcement modes."""

    SAFE = "safe"
    POWER = "power"


class CommandType(str, Enum):
    """Allowed command types in revise scripts."""

    MODIFY = "modify"
    ANNOTATE = "annotate"


@dataclass
class Policy:
    """Safety policy for TaskMan operations.

    Defines what fields and operations are allowed in revise scripts
    and other LLM-driven modifications.
    """

    mode: PolicyMode = PolicyMode.SAFE

    # Core allowed fields (SAFE mode)
    allowed_core_fields: set[str] = field(
        default_factory=lambda: {
            "tags",
            "project",
            "priority",
            "due",
            "until",
            "depends",
        }
    )

    # Optional fields (can be enabled in SAFE mode)
    optional_fields: set[str] = field(
        default_factory=lambda: {
            "wait",
            "scheduled",
        }
    )

    # Fields allowed only in POWER mode
    power_fields: set[str] = field(
        default_factory=lambda: {
            "start",
            "stop",
            "recur",
        }
    )

    # Fields that are NEVER allowed to be modified
    forbidden_fields: set[str] = field(
        default_factory=lambda: {
            "description",  # Disallow description changes by default
            "entry",  # Task creation time
            "uuid",  # Task UUID
            "id",  # Task ID
        }
    )

    # Allowed commands
    allowed_commands: set[CommandType] = field(
        default_factory=lambda: {
            CommandType.MODIFY,
            CommandType.ANNOTATE,
        }
    )

    # Whether to allow optional fields
    enable_optional_fields: bool = False

    # Whether to allow UDAs (always true when registry is provided)
    allow_udas: bool = True

    # Whether to allow bulk operations (multi-task selectors)
    allow_bulk_operations: bool = False

    def is_field_allowed(self, field_name: str, uda_names: set[str] | None = None) -> bool:
        """Check if a field is allowed to be modified.

        Args:
            field_name: Name of the field to check
            uda_names: Set of known UDA names from the registry

        Returns:
            True if the field can be modified, False otherwise
        """
        # Check forbidden first
        if field_name in self.forbidden_fields:
            return False

        # Check if it's a UDA
        if uda_names and field_name in uda_names:
            return self.allow_udas

        # Check core allowed fields
        if field_name in self.allowed_core_fields:
            return True

        # Check optional fields
        if field_name in self.optional_fields:
            return self.enable_optional_fields

        # Check power fields
        if field_name in self.power_fields:
            return self.mode == PolicyMode.POWER

        # Unknown field - reject
        return False

    def is_command_allowed(self, command_type: CommandType) -> bool:
        """Check if a command type is allowed.

        Args:
            command_type: The type of command to check

        Returns:
            True if the command is allowed, False otherwise
        """
        return command_type in self.allowed_commands

    def get_allowed_fields_description(self, uda_names: set[str] | None = None) -> str:
        """Get a human-readable description of allowed fields.

        Args:
            uda_names: Set of known UDA names from the registry

        Returns:
            Description string for use in prompts
        """
        fields = list(self.allowed_core_fields)

        if self.enable_optional_fields:
            fields.extend(self.optional_fields)

        if self.mode == PolicyMode.POWER:
            fields.extend(self.power_fields)

        if uda_names and self.allow_udas:
            fields.extend(sorted(uda_names))

        return ", ".join(sorted(fields))

    @classmethod
    def safe(cls, enable_optional: bool = False) -> Policy:
        """Create a SAFE mode policy.

        Args:
            enable_optional: Whether to enable optional fields (wait, scheduled)

        Returns:
            Policy configured for SAFE mode
        """
        return cls(
            mode=PolicyMode.SAFE,
            enable_optional_fields=enable_optional,
        )

    @classmethod
    def power(cls) -> Policy:
        """Create a POWER mode policy.

        Returns:
            Policy configured for POWER mode
        """
        return cls(
            mode=PolicyMode.POWER,
            enable_optional_fields=True,
        )


# Default policies
DEFAULT_SAFE_POLICY = Policy.safe()
DEFAULT_POWER_POLICY = Policy.power()


def get_policy(mode: str = "safe", enable_optional: bool = False) -> Policy:
    """Get a policy instance based on mode string.

    Args:
        mode: "safe" or "power"
        enable_optional: Whether to enable optional fields

    Returns:
        Configured Policy instance

    Raises:
        ValueError: If mode is invalid
    """
    if mode == "safe":
        return Policy.safe(enable_optional=enable_optional)
    elif mode == "power":
        return Policy.power()
    else:
        raise ValueError(f"Invalid policy mode: {mode}. Must be 'safe' or 'power'.")
