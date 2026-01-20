"""Tests for revise script parser."""

from __future__ import annotations

import pytest

from taskman.parser import (
    CommandAST,
    CommandType,
    FieldOperation,
    ParseError,
    parse_revise_script,
)


def test_parse_simple_modify():
    """Test parsing a simple modify command."""
    script = "task 123 modify project:foo"
    commands = parse_revise_script(script)

    assert len(commands) == 1
    cmd = commands[0]
    assert cmd.command_type == CommandType.MODIFY
    assert cmd.selector == "123"
    assert len(cmd.operations) == 1
    assert cmd.operations[0].field == "project"
    assert cmd.operations[0].value == "foo"


def test_parse_tag_operations():
    """Test parsing tag add/remove operations."""
    script = "task 456 modify +newtag -oldtag"
    commands = parse_revise_script(script)

    assert len(commands) == 1
    cmd = commands[0]
    assert len(cmd.operations) == 2

    # Check tag addition
    assert cmd.operations[0].field == "tags"
    assert cmd.operations[0].operation == "add"
    assert cmd.operations[0].value == "newtag"

    # Check tag removal
    assert cmd.operations[1].field == "tags"
    assert cmd.operations[1].operation == "remove"
    assert cmd.operations[1].value == "oldtag"


def test_parse_annotate():
    """Test parsing annotate command."""
    script = 'task abc123 annotate "This is a test annotation"'
    commands = parse_revise_script(script)

    assert len(commands) == 1
    cmd = commands[0]
    assert cmd.command_type == CommandType.ANNOTATE
    assert cmd.selector == "abc123"
    assert cmd.annotation_text == "This is a test annotation"


def test_parse_multi_line():
    """Test parsing multiple commands."""
    script = """
    task 123 modify project:foo +tag1
    task 456 annotate Note added
    task 789 modify priority:H
    """
    commands = parse_revise_script(script)

    assert len(commands) == 3
    assert commands[0].command_type == CommandType.MODIFY
    assert commands[1].command_type == CommandType.ANNOTATE
    assert commands[2].command_type == CommandType.MODIFY


def test_parse_comments_and_blank_lines():
    """Test that comments and blank lines are ignored."""
    script = """
    # This is a comment
    task 123 modify project:foo

    # Another comment
    task 456 annotate Test
    """
    commands = parse_revise_script(script)

    assert len(commands) == 2


def test_parse_error_invalid_command():
    """Test that invalid commands raise ParseError."""
    script = "task 123 delete"
    with pytest.raises(ParseError):
        parse_revise_script(script)


def test_parse_error_missing_selector():
    """Test that missing selector raises ParseError."""
    script = "task modify project:foo"
    with pytest.raises(ParseError):
        parse_revise_script(script)


def test_parse_uuid_selector():
    """Test parsing with UUID selector."""
    uuid = "12345678-1234-1234-1234-123456789abc"
    script = f"task {uuid} modify priority:H"
    commands = parse_revise_script(script)

    assert len(commands) == 1
    assert commands[0].selector == uuid
