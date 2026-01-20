"""Tests for policy and allowlist."""

from __future__ import annotations

from taskman.policy import Policy, PolicyMode, get_policy


def test_safe_policy_allows_core_fields():
    """Test that SAFE mode allows core fields."""
    policy = Policy.safe()

    assert policy.is_field_allowed("tags")
    assert policy.is_field_allowed("project")
    assert policy.is_field_allowed("priority")
    assert policy.is_field_allowed("due")


def test_safe_policy_forbids_description():
    """Test that SAFE mode forbids description changes."""
    policy = Policy.safe()

    assert not policy.is_field_allowed("description")
    assert not policy.is_field_allowed("entry")
    assert not policy.is_field_allowed("uuid")


def test_safe_policy_optional_fields():
    """Test optional fields in SAFE mode."""
    policy_no_optional = Policy.safe(enable_optional=False)
    policy_with_optional = Policy.safe(enable_optional=True)

    assert not policy_no_optional.is_field_allowed("wait")
    assert policy_with_optional.is_field_allowed("wait")
    assert policy_with_optional.is_field_allowed("scheduled")


def test_power_policy_allows_more():
    """Test that POWER mode allows additional fields."""
    policy = Policy.power()

    # Should allow core fields
    assert policy.is_field_allowed("tags")

    # Should allow optional fields
    assert policy.is_field_allowed("wait")

    # Should allow power fields
    assert policy.is_field_allowed("start")
    assert policy.is_field_allowed("recur")

    # Should still forbid description
    assert not policy.is_field_allowed("description")


def test_policy_allows_udas():
    """Test that policies allow UDAs from registry."""
    policy = Policy.safe()
    uda_names = {"context", "why", "stakeholder"}

    assert policy.is_field_allowed("context", uda_names)
    assert policy.is_field_allowed("why", uda_names)
    assert not policy.is_field_allowed("unknown_field", uda_names)


def test_get_policy_helper():
    """Test get_policy helper function."""
    safe = get_policy("safe")
    assert safe.mode == PolicyMode.SAFE

    power = get_policy("power")
    assert power.mode == PolicyMode.POWER
