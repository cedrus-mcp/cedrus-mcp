"""Unit tests for argdown rendering."""

from cedrus.graph.argument_map import ArgumentMap
from cedrus.graph.rendering import render_argdown, render_argdown_node
from cedrus.models import ClaimNode, ArgumentNode, Proposition


def test_render_empty_graph() -> None:
    """Test rendering an empty graph."""
    arg_map = ArgumentMap()
    
    result = render_argdown(arg_map)
    
    assert isinstance(result, str)


def test_render_graph_with_claims() -> None:
    """Test rendering a graph with claims."""
    arg_map = ArgumentMap()
    
    prop1 = Proposition(content="Claim 1")
    prop2 = Proposition(content="Claim 2")
    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)
    
    claim1 = ClaimNode(label="C1", proposition_id=prop1.id)
    claim2 = ClaimNode(label="C2", proposition_id=prop2.id)
    
    arg_map.add_claim(claim1)
    arg_map.add_claim(claim2)
    
    result = render_argdown(arg_map)
    
    assert "C1" in result
    assert "C2" in result


def test_render_graph_label_only() -> None:
    """Test rendering with label_only=True."""
    arg_map = ArgumentMap()
    
    prop = Proposition(content="Long proposition")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg_map.add_claim(claim)
    
    result = render_argdown(arg_map, label_only=True)
    
    assert "C1" in result
    # Proposition text should not be included in label-only mode
    assert "Long proposition" not in result


def test_render_graph_with_details() -> None:
    """Test rendering with full details."""
    arg_map = ArgumentMap()
    
    prop = Proposition(content="Test claim")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg_map.add_claim(claim)
    
    result = render_argdown(arg_map, label_only=False)
    
    assert "C1" in result
    assert "Test claim" in result


def test_render_single_node() -> None:
    """Test rendering a single node."""
    arg_map = ArgumentMap()
    
    prop = Proposition(content="Test claim")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg_map.add_claim(claim)
    
    result = render_argdown_node(arg_map, label="C1", details=True)
    
    assert "C1" in result
    assert "Test claim" in result


def test_render_node_without_details() -> None:
    """Test rendering a node without details."""
    arg_map = ArgumentMap()
    
    prop = Proposition(content="Test claim")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg_map.add_claim(claim)
    
    result = render_argdown_node(arg_map, label="C1", details=False)
    
    assert "C1" in result


def test_render_graph_with_relations() -> None:
    """Test rendering includes relations."""
    arg_map = ArgumentMap()
    
    prop = Proposition(content="Claim")
    arg_map.add_proposition(prop)
    claim = ClaimNode(label="C1", proposition_id=prop.id)
    arg = ArgumentNode(label="A1", gist="Argument")
    
    arg_map.add_claim(claim)
    arg_map.add_argument(arg)
    arg_map.add_support_relation(from_label="A1", to_label="C1")
    
    result = render_argdown(arg_map)
    
    # Should show both nodes
    assert "C1" in result
    assert "A1" in result
