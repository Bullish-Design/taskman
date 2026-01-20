"""Validation logic for revise scripts and commands."""

from __future__ import annotations

from dataclasses import dataclass, field

from taskman.export import resolve_selector, SelectorResolutionError
from taskman.parser import CommandAST, CommandType
from taskman.policy import Policy


class ValidationError(Exception):
    """Error during validation."""


@dataclass
class ValidationIssue:
    """A single validation issue."""

    severity: str  # "error", "warning"
    message: str
    command_index: int | None = None
    field: str | None = None


@dataclass
class ValidationResult:
    """Result of validation."""

    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    normalized_commands: list[CommandAST] = field(default_factory=list)

    def add_error(
        self,
        message: str,
        command_index: int | None = None,
        field: str | None = None,
    ) -> None:
        """Add an error issue."""
        self.issues.append(
            ValidationIssue(
                severity="error",
                message=message,
                command_index=command_index,
                field=field,
            )
        )
        self.is_valid = False

    def add_warning(
        self,
        message: str,
        command_index: int | None = None,
        field: str | None = None,
    ) -> None:
        """Add a warning issue."""
        self.issues.append(
            ValidationIssue(
                severity="warning",
                message=message,
                command_index=command_index,
                field=field,
            )
        )

    def get_error_summary(self) -> str:
        """Get a summary of all errors."""
        errors = [i for i in self.issues if i.severity == "error"]
        if not errors:
            return "No errors"

        lines = [f"Found {len(errors)} validation error(s):"]
        for i, issue in enumerate(errors, start=1):
            prefix = f"  {i}. "
            if issue.command_index is not None:
                prefix += f"Command {issue.command_index}: "
            if issue.field:
                prefix += f"Field '{issue.field}': "
            lines.append(f"{prefix}{issue.message}")

        return "\n".join(lines)


class ReviseScriptValidator:
    """Validator for revise scripts."""

    def __init__(self, policy: Policy, uda_names: set[str] | None = None):
        """Initialize validator.

        Args:
            policy: Safety policy to enforce
            uda_names: Set of known UDA names from registry
        """
        self.policy = policy
        self.uda_names = uda_names or set()

    def validate(self, commands: list[CommandAST]) -> ValidationResult:
        """Validate a list of commands.

        Args:
            commands: List of parsed commands

        Returns:
            ValidationResult with issues and normalized commands
        """
        result = ValidationResult(is_valid=True)

        for i, cmd in enumerate(commands):
            # Validate command type
            if not self._validate_command_type(cmd, result, i):
                continue

            # Validate selector and normalize to UUID
            normalized_cmd = self._validate_and_normalize_selector(cmd, result, i)
            if normalized_cmd is None:
                continue

            # Validate fields (for modify commands)
            if cmd.is_modify:
                self._validate_modify_fields(cmd, result, i)

            # Add to normalized commands if still valid
            if result.is_valid:
                result.normalized_commands.append(normalized_cmd)

        return result

    def _validate_command_type(
        self,
        cmd: CommandAST,
        result: ValidationResult,
        index: int,
    ) -> bool:
        """Validate that command type is allowed.

        Returns:
            True if valid, False otherwise
        """
        cmd_type = CommandType(cmd.command_type.value)
        if not self.policy.is_command_allowed(cmd_type):
            result.add_error(
                f"Command type '{cmd.command_type}' not allowed by policy",
                command_index=index,
            )
            return False
        return True

    def _validate_and_normalize_selector(
        self,
        cmd: CommandAST,
        result: ValidationResult,
        index: int,
    ) -> CommandAST | None:
        """Validate selector and normalize to UUID.

        Returns:
            Normalized command with UUID selector, or None if validation failed
        """
        try:
            uuid = resolve_selector(cmd.selector)
            # Create a new command with normalized selector
            return CommandAST(
                command_type=cmd.command_type,
                selector=uuid,
                operations=cmd.operations,
                annotation_text=cmd.annotation_text,
            )
        except SelectorResolutionError as e:
            result.add_error(
                f"Cannot resolve selector '{cmd.selector}': {e}",
                command_index=index,
            )
            return None

    def _validate_modify_fields(
        self,
        cmd: CommandAST,
        result: ValidationResult,
        index: int,
    ) -> None:
        """Validate fields in a modify command."""
        if not cmd.operations:
            return

        for op in cmd.operations:
            # Check if field is allowed
            if not self.policy.is_field_allowed(op.field, self.uda_names):
                result.add_error(
                    f"Field '{op.field}' not allowed by policy. "
                    f"Allowed fields: {self.policy.get_allowed_fields_description(self.uda_names)}",
                    command_index=index,
                    field=op.field,
                )

            # Validate depends field specially
            if op.field == "depends" and op.value:
                self._validate_depends_value(op.value, result, index)

    def _validate_depends_value(
        self,
        depends_value: str,
        result: ValidationResult,
        index: int,
    ) -> None:
        """Validate a depends field value.

        Ensures all dependency UUIDs/IDs can be resolved.
        """
        # Split by comma
        dep_selectors = [d.strip() for d in depends_value.split(",")]

        for dep_sel in dep_selectors:
            try:
                resolve_selector(dep_sel)
            except SelectorResolutionError as e:
                result.add_error(
                    f"Cannot resolve dependency '{dep_sel}': {e}",
                    command_index=index,
                    field="depends",
                )


def validate_commands(
    commands: list[CommandAST],
    policy: Policy,
    uda_names: set[str] | None = None,
) -> ValidationResult:
    """Validate a list of commands.

    Args:
        commands: List of parsed commands
        policy: Safety policy to enforce
        uda_names: Set of known UDA names from registry

    Returns:
        ValidationResult with issues and normalized commands
    """
    validator = ReviseScriptValidator(policy=policy, uda_names=uda_names)
    return validator.validate(commands)
