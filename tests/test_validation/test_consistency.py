"""Tests for consistency validation."""

import pytest

from cedrus.backend.graph.argument_map import ArgumentMap
from cedrus.backend.models import ClaimNode, Proposition
from cedrus.backend.validation.consistency import check_consistency
from cedrus.tools.runtime.tool_context import ToolContext


def test_check_consistency_empty_map(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test consistency check on empty map."""
    issues = check_consistency(empty_map, elaborate_context)
    assert issues == 0


def test_check_consistency_single_proposition(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test consistency check with single proposition."""
    prop = Proposition(content="Test proposition")
    empty_map.add_proposition(prop)
    issues = check_consistency(empty_map, elaborate_context)
    assert issues == 0


def test_check_consistency_equivalent_propositions_no_contradiction(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test that equivalent propositions without contradiction don't generate issues."""
    prop1 = Proposition(content="Proposition A")
    prop2 = Proposition(content="Proposition A (rephrased)")
    empty_map.add_proposition(prop1)
    empty_map.add_proposition(prop2)

    # Make them equivalent
    empty_map.add_equivalence(prop1.id, prop2.id)

    issues = check_consistency(empty_map, elaborate_context)
    assert issues == 0


def test_check_consistency_detects_self_contradictory_equivalence_class(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test detection of self-contradictory equivalence class."""
    # Create three propositions
    prop1 = Proposition(content="P")
    prop2 = Proposition(content="Q")
    prop3 = Proposition(content="Not P")

    empty_map.add_proposition(prop1)
    empty_map.add_proposition(prop2)
    empty_map.add_proposition(prop3)

    # First establish that P and Not-P are contradictory
    empty_map.add_negation(prop1.id, prop3.id)

    # Now make P and Q equivalent
    empty_map.add_equivalence(prop1.id, prop2.id)

    # Directly add equivalence edge Q ≡ Not-P to bypass API safety check
    # This creates a self-contradictory equivalence class: {P, Q, Not-P}
    # where P and Not-P have a negation relation
    from cedrus.backend.models.relations import LogicalRelation

    relation = LogicalRelation(_type="equivalence")
    empty_map.proposition_graph.add_edge(prop2.id, prop3.id, **relation.model_dump(by_alias=True))

    # Should detect self-contradictory equivalence class
    issues = check_consistency(empty_map, elaborate_context, fix=False)

    assert issues > 0


def test_check_consistency_respects_max_issues(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test that max_issues parameter limits reported issues."""
    # Create multiple self-contradictory equivalence classes
    from cedrus.backend.models.relations import LogicalRelation

    for i in range(5):
        p1 = Proposition(content=f"Prop{i}")
        p2 = Proposition(content=f"Not Prop{i}")
        empty_map.add_proposition(p1)
        empty_map.add_proposition(p2)

        # First add negation relation
        empty_map.add_negation(p1.id, p2.id)

        # Then directly add equivalence edge to bypass API safety check
        relation = LogicalRelation(_type="equivalence")
        empty_map.proposition_graph.add_edge(p1.id, p2.id, **relation.model_dump(by_alias=True))

    # With max_issues=2, should stop after 2 issues
    issues = check_consistency(empty_map, elaborate_context, max_issues=2)

    assert issues <= 2


def test_check_consistency_independent_propositions(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test that independent propositions don't generate consistency issues."""
    # Create several independent propositions
    p1 = Proposition(content="Independent A")
    p2 = Proposition(content="Independent B")
    p3 = Proposition(content="Independent C")
    empty_map.add_proposition(p1)
    empty_map.add_proposition(p2)
    empty_map.add_proposition(p3)

    # No equivalence or negation relations

    issues = check_consistency(empty_map, elaborate_context)
    assert issues == 0


def test_check_consistency_contradictory_but_not_equivalent(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test that contradictory propositions in different equivalence classes are valid."""
    # Create two contradictory propositions
    p1 = Proposition(content="P")
    p2 = Proposition(content="Not P")

    empty_map.add_proposition(p1)
    empty_map.add_proposition(p2)

    # Mark as contradictory but DON'T make them equivalent
    empty_map.add_negation(p1.id, p2.id)

    # This is valid - contradictory propositions should exist
    issues = check_consistency(empty_map, elaborate_context)
    assert issues == 0
