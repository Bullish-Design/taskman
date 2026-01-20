"""Revise script parser with safe grammar."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from enum import Enum


class CommandType(str, Enum):
    """Types of commands allowed in revise scripts."""

    MODIFY = "modify"
    ANNOTATE = "annotate"


class ParseError(Exception):
    """Error parsing revise script."""


@dataclass
class FieldOperation:
    """A single field operation in a modify command."""

    field: str
    operation: str  # "set", "add", "remove"
    value: str | None = None

    @classmethod
    def from_token(cls, token: str) -> FieldOperation:
        """Parse a field operation from a token.

        Examples:
            "project:myproject" -> FieldOperation("project", "set", "myproject")
            "+mytag" -> FieldOperation("tags", "add", "mytag")
            "-oldtag" -> FieldOperation("tags", "remove", "oldtag")
            "priority:H" -> FieldOperation("priority", "set", "H")
        """
        # Tag addition
        if token.startswith("+"):
            return cls(field="tags", operation="add", value=token[1:])

        # Tag removal
        if token.startswith("-"):
            return cls(field="tags", operation="remove", value=token[1:])

        # Field assignment (key:value)
        if ":" in token:
            field, value = token.split(":", 1)
            return cls(field=field, operation="set", value=value)

        raise ParseError(f"Invalid field operation token: {token}")


@dataclass
class CommandAST:
    """Abstract Syntax Tree node for a command."""

    command_type: CommandType
    selector: str
    operations: list[FieldOperation] | None = None  # For modify
    annotation_text: str | None = None  # For annotate

    @property
    def is_modify(self) -> bool:
        """Check if this is a modify command."""
        return self.command_type == CommandType.MODIFY

    @property
    def is_annotate(self) -> bool:
        """Check if this is an annotate command."""
        return self.command_type == CommandType.ANNOTATE


class ReviseScriptParser:
    """Parser for revise scripts.

    Parses a subset of Taskwarrior commands:
    - task <selector> modify <field_ops...>
    - task <selector> annotate <text...>

    Safety features:
    - No shell execution or evaluation
    - Strict grammar enforcement
    - No command chaining or piping
    - One command per line
    """

    # Pattern for valid selectors (uuid, numeric id, or simple filter)
    SELECTOR_PATTERN = re.compile(
        r"^([0-9a-f\-]{36}|[0-9]+|[\w\+\-:]+)$",
        re.IGNORECASE,
    )

    def __init__(self) -> None:
        """Initialize parser."""
        pass

    def parse(self, script: str) -> list[CommandAST]:
        """Parse a revise script into AST.

        Args:
            script: Multi-line revise script

        Returns:
            List of CommandAST nodes

        Raises:
            ParseError: If script contains invalid syntax
        """
        commands = []
        lines = script.strip().split("\n")

        for line_num, line in enumerate(lines, start=1):
            # Skip empty lines and comments
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                cmd = self._parse_line(line)
                commands.append(cmd)
            except ParseError as e:
                raise ParseError(f"Line {line_num}: {e}") from e

        return commands

    def _parse_line(self, line: str) -> CommandAST:
        """Parse a single command line.

        Args:
            line: Single command line

        Returns:
            CommandAST node

        Raises:
            ParseError: If line is invalid
        """
        # Use shlex to handle quoted strings properly
        try:
            tokens = shlex.split(line)
        except ValueError as e:
            raise ParseError(f"Invalid quoting: {e}") from e

        if not tokens:
            raise ParseError("Empty command")

        # First token should be 'task'
        if tokens[0] != "task":
            raise ParseError(f"Commands must start with 'task', got: {tokens[0]}")

        if len(tokens) < 3:
            raise ParseError("Incomplete command (need at least: task <selector> <command>)")

        selector = tokens[1]
        command = tokens[2]
        args = tokens[3:]

        # Validate selector
        if not self._is_valid_selector(selector):
            raise ParseError(f"Invalid selector: {selector}")

        # Parse based on command type
        if command == "modify":
            return self._parse_modify(selector, args)
        elif command == "annotate":
            return self._parse_annotate(selector, args)
        else:
            raise ParseError(f"Unknown command: {command}. Allowed: modify, annotate")

    def _is_valid_selector(self, selector: str) -> bool:
        """Check if a selector is valid.

        Args:
            selector: Selector string

        Returns:
            True if valid, False otherwise
        """
        return bool(self.SELECTOR_PATTERN.match(selector))

    def _parse_modify(self, selector: str, args: list[str]) -> CommandAST:
        """Parse a modify command.

        Args:
            selector: Task selector
            args: Field operation tokens

        Returns:
            CommandAST for modify

        Raises:
            ParseError: If invalid
        """
        if not args:
            raise ParseError("modify command requires at least one field operation")

        operations = []
        for arg in args:
            try:
                op = FieldOperation.from_token(arg)
                operations.append(op)
            except ParseError as e:
                raise ParseError(f"Invalid field operation '{arg}': {e}") from e

        return CommandAST(
            command_type=CommandType.MODIFY,
            selector=selector,
            operations=operations,
        )

    def _parse_annotate(self, selector: str, args: list[str]) -> CommandAST:
        """Parse an annotate command.

        Args:
            selector: Task selector
            args: Annotation text tokens

        Returns:
            CommandAST for annotate

        Raises:
            ParseError: If invalid
        """
        if not args:
            raise ParseError("annotate command requires annotation text")

        # Join all args as annotation text
        annotation_text = " ".join(args)

        return CommandAST(
            command_type=CommandType.ANNOTATE,
            selector=selector,
            annotation_text=annotation_text,
        )


def parse_revise_script(script: str) -> list[CommandAST]:
    """Parse a revise script.

    Args:
        script: Multi-line revise script

    Returns:
        List of CommandAST nodes

    Raises:
        ParseError: If script is invalid
    """
    parser = ReviseScriptParser()
    return parser.parse(script)


def command_to_string(cmd: CommandAST) -> str:
    """Convert a CommandAST back to string representation.

    Args:
        cmd: Command AST node

    Returns:
        String representation
    """
    parts = ["task", cmd.selector]

    if cmd.is_modify and cmd.operations:
        parts.append("modify")
        for op in cmd.operations:
            if op.operation == "add":
                parts.append(f"+{op.value}")
            elif op.operation == "remove":
                parts.append(f"-{op.value}")
            elif op.operation == "set" and op.value:
                parts.append(f"{op.field}:{op.value}")

    elif cmd.is_annotate and cmd.annotation_text:
        parts.append("annotate")
        # Quote if contains spaces
        if " " in cmd.annotation_text:
            parts.append(f'"{cmd.annotation_text}"')
        else:
            parts.append(cmd.annotation_text)

    return " ".join(parts)
