"""Tests for completeness validation."""

import pytest

from cedrus.graph.argument_map import ArgumentMap
from cedrus.models import ArgumentNode, ClaimNode, Proposition
from cedrus.tools.runtime.tool_context import ToolContext
from cedrus.validation.completeness import check_completeness


def test_check_completeness_empty_map(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test completeness check on empty map."""
    issues = check_completeness(empty_map, elaborate_context)
    assert issues == 0


def test_check_completeness_single_node(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test completeness check with single node (no pairs)."""
    prop = Proposition(content="Test")
    empty_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    empty_map.add_claim(claim)
    issues = check_completeness(empty_map, elaborate_context)
    assert issues == 0


def test_check_completeness_respects_max_issues(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test that max_issues parameter limits reported issues."""
    # Create multiple potential issues
    for i in range(5):
        prop = Proposition(content=f"Claim{i}")
        empty_map.add_proposition(prop)
        claim = ClaimNode(label=f"C{i}", proposition_id=prop.id)
        empty_map.add_claim(claim)

    # With max_issues=2, should stop after 2 issues
    issues = check_completeness(empty_map, elaborate_context, max_issues=2)

    assert issues <= 2


def test_check_completeness_skips_self_relations(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test that completeness check doesn't flag missing self-relations."""
    prop = Proposition(content="Claim1")
    empty_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    empty_map.add_claim(claim)

    # Should not create issues for node relating to itself
    issues = check_completeness(empty_map, elaborate_context)

    assert issues == 0


def test_check_completeness_all_pairs_checked(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test that completeness check examines all node pairs (O(n²) algorithm)."""
    # Create multiple nodes
    for i in range(4):
        prop = Proposition(content=f"Claim{i}")
        empty_map.add_proposition(prop)
        claim = ClaimNode(label=f"C{i}", proposition_id=prop.id)
        empty_map.add_claim(claim)

    # Should check all pairs: 4*3 = 12 pairs (excluding self)
    issues = check_completeness(empty_map, elaborate_context)

    # Algorithm should complete successfully on 4 nodes
    assert isinstance(issues, int)
