"""Tests for connectivity validation."""

import pytest

from cedrus.backend.graph.argument_map import ArgumentMap
from cedrus.backend.models import ClaimNode, Proposition
from cedrus.backend.validation.connectivity import check_connectivity
from cedrus.tools.runtime.tool_context import ToolContext


def add_claim_node(arg_map: ArgumentMap, content: str) -> str:
    """Helper to add a claim node with given content."""
    prop = Proposition(content=content)
    arg_map.add_proposition(prop)
    label = f"C{len(arg_map.argument_graph.nodes) + 1}"
    claim = ClaimNode(label=label, proposition_id=prop.id)
    arg_map.add_claim(claim)
    return label


def test_check_connectivity_empty_map(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test connectivity check on empty map."""
    issues = check_connectivity(empty_map, elaborate_context)
    assert issues == 0


def test_check_connectivity_single_node(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test connectivity check with single node (trivially connected)."""
    prop = Proposition(content="Single Claim")
    empty_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    empty_map.add_claim(claim)
    issues = check_connectivity(empty_map, elaborate_context)
    assert issues == 0


def test_check_connectivity_two_connected_nodes(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test connectivity check with two connected nodes."""
    claim1 = add_claim_node(empty_map, "Claim1")
    claim2 = add_claim_node(empty_map, "Claim2")

    # Connect them with support relation
    empty_map.add_support_relation(claim1, claim2)

    # Should be fully connected
    issues = check_connectivity(empty_map, elaborate_context)
    assert issues == 0


def test_check_connectivity_two_disconnected_nodes(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test detection of disconnected graph."""
    claim1 = add_claim_node(empty_map, "Claim1")
    claim2 = add_claim_node(empty_map, "Claim2")

    # Don't connect them - creates 2 components

    # Should detect disconnected components
    issues = check_connectivity(empty_map, elaborate_context)
    assert issues == 1


def test_check_connectivity_three_nodes_two_components(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test detection of multiple components."""
    # Create first component (2 connected nodes)
    c1 = add_claim_node(empty_map, "Claim1")
    c2 = add_claim_node(empty_map, "Claim2")
    empty_map.add_support_relation(c1, c2)

    # Create second component (isolated node)
    c3 = add_claim_node(empty_map, "Claim3")

    # Should detect 2 components
    issues = check_connectivity(empty_map, elaborate_context)
    assert issues == 1


def test_check_connectivity_fully_connected_graph(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test that fully connected graph has no connectivity issues."""
    # Create a chain of connected nodes
    nodes = []
    for i in range(5):
        label = add_claim_node(empty_map, f"Claim{i}")
        nodes.append(label)

    # Connect them in a chain
    for i in range(len(nodes) - 1):
        empty_map.add_support_relation(nodes[i], nodes[i + 1])

    # Should be fully connected
    issues = check_connectivity(empty_map, elaborate_context)
    assert issues == 0


def test_check_connectivity_star_topology(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test connectivity with star topology (one central node)."""
    # Create central node
    center = add_claim_node(empty_map, "Center")

    # Create peripheral nodes all connected to center
    for i in range(4):
        peripheral = add_claim_node(empty_map, f"Peripheral{i}")
        empty_map.add_support_relation(peripheral, center)

    # Should be fully connected via center
    issues = check_connectivity(empty_map, elaborate_context)
    assert issues == 0


def test_check_connectivity_reports_component_roots(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test that connectivity check identifies component roots."""
    # Create two separate trees
    root1 = add_claim_node(empty_map, "Root1")
    child1 = add_claim_node(empty_map, "Child1")
    empty_map.add_support_relation(child1, root1)

    root2 = add_claim_node(empty_map, "Root2")
    child2 = add_claim_node(empty_map, "Child2")
    empty_map.add_support_relation(child2, root2)

    # Should detect disconnected components and identify roots
    issues = check_connectivity(empty_map, elaborate_context)
    assert issues == 1


def test_check_connectivity_generates_warning_level_issues(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test that connectivity issues are warnings (not errors)."""
    # Create disconnected graph
    add_claim_node(empty_map, "Isolated1")
    add_claim_node(empty_map, "Isolated2")

    # Should generate warning
    issues = check_connectivity(empty_map, elaborate_context)
    assert issues == 1


def test_check_connectivity_fix_parameter_has_no_effect(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test that fix parameter doesn't auto-fix connectivity (can't be auto-fixed)."""
    # Create disconnected graph
    add_claim_node(empty_map, "Isolated1")
    add_claim_node(empty_map, "Isolated2")

    # Try with fix=True
    issues_with_fix = check_connectivity(empty_map, elaborate_context, fix=True)

    # Should still report issue (connectivity can't be auto-fixed)
    assert issues_with_fix == 1


def test_check_connectivity_respects_max_issues(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test that max_issues parameter is respected."""
    # Create disconnected graph (which generates 1 issue)
    add_claim_node(empty_map, "Isolated1")
    add_claim_node(empty_map, "Isolated2")

    # With max_issues=1
    issues = check_connectivity(empty_map, elaborate_context, max_issues=1)
    assert issues <= 1


def test_check_connectivity_bidirectional_relations(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test connectivity with bidirectional relations."""
    c1 = add_claim_node(empty_map, "Claim1")
    c2 = add_claim_node(empty_map, "Claim2")

    # Create mutual support
    empty_map.add_support_relation(c1, c2)
    empty_map.add_support_relation(c2, c1)

    # Should still be connected
    issues = check_connectivity(empty_map, elaborate_context)
    assert issues == 0


def test_check_connectivity_cyclic_graph(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test connectivity with cycles."""
    # Create a cycle: A -> B -> C -> A
    c1 = add_claim_node(empty_map, "Claim1")
    c2 = add_claim_node(empty_map, "Claim2")
    c3 = add_claim_node(empty_map, "Claim3")

    empty_map.add_support_relation(c1, c2)
    empty_map.add_support_relation(c2, c3)
    empty_map.add_support_relation(c3, c1)

    # Should be connected despite cycle
    issues = check_connectivity(empty_map, elaborate_context)
    assert issues == 0


def test_check_connectivity_mixed_relation_types(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test connectivity with both support and attack relations."""
    c1 = add_claim_node(empty_map, "Claim1")
    c2 = add_claim_node(empty_map, "Claim2")
    c3 = add_claim_node(empty_map, "Claim3")

    # Connect with mixed relations
    empty_map.add_support_relation(c1, c2)
    empty_map.add_attack_relation(c2, c3)

    # Should be connected (relation type doesn't matter for connectivity)
    issues = check_connectivity(empty_map, elaborate_context)
    assert issues == 0


def test_check_connectivity_large_disconnected_graph(
    empty_map: ArgumentMap, elaborate_context: ToolContext
) -> None:
    """Test connectivity with many disconnected components."""
    # Create 5 isolated nodes (5 components)
    for i in range(5):
        add_claim_node(empty_map, f"Isolated{i}")

    # Should detect multiple components
    issues = check_connectivity(empty_map, elaborate_context)
    assert issues == 1  # Reports 1 issue for disconnected graph
