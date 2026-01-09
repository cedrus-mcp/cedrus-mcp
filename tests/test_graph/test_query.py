"""Unit tests for graph query operations."""

from cedrus.graph.argument_map import ArgumentMap
from cedrus.models import ClaimNode, ArgumentNode, Proposition


def test_get_k_neighborhood_k1() -> None:
    """Test getting 1-neighborhood of a node."""
    arg_map = ArgumentMap()
    
    # Create chain: A1 -> C1 -> C2
    prop1 = Proposition(content="Claim 1")
    prop2 = Proposition(content="Claim 2")
    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)
    
    c1 = ClaimNode(label="C1", proposition_id=prop1.id)
    c2 = ClaimNode(label="C2", proposition_id=prop2.id)
    a1 = ArgumentNode(label="A1", gist="Argument 1")
    
    arg_map.add_claim(c1)
    arg_map.add_claim(c2)
    arg_map.add_argument(a1)
    
    arg_map.add_support_relation(from_label="A1", to_label="C1")
    arg_map.add_support_relation(from_label="C1", to_label="C2")
    
    neighborhood = arg_map.get_k_neighborhood("C1", k=1)
    
    # Should include C1 and its immediate neighbors (A1, C2)
    assert "C1" in neighborhood
    assert "A1" in neighborhood
    assert "C2" in neighborhood


def test_get_k_neighborhood_k0() -> None:
    """Test getting 0-neighborhood returns just the node."""
    arg_map = ArgumentMap()
    
    prop = Proposition(content="Claim 1")
    arg_map.add_proposition(prop)
    c1 = ClaimNode(label="C1", proposition_id=prop.id)
    arg_map.add_claim(c1)
    
    neighborhood = arg_map.get_k_neighborhood("C1", k=0)
    
    assert len(neighborhood) == 1
    assert "C1" in neighborhood


def test_connected_components_single_component() -> None:
    """Test graph with single connected component."""
    arg_map = ArgumentMap()
    
    # Create connected graph
    prop1 = Proposition(content="Claim 1")
    prop2 = Proposition(content="Claim 2")
    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)
    
    c1 = ClaimNode(label="C1", proposition_id=prop1.id)
    c2 = ClaimNode(label="C2", proposition_id=prop2.id)
    
    arg_map.add_claim(c1)
    arg_map.add_claim(c2)
    arg_map.add_support_relation(from_label="C1", to_label="C2")
    
    components = arg_map.connected_components()
    
    assert len(components) == 1
    assert len(components[0]) == 2


def test_connected_components_multiple() -> None:
    """Test graph with multiple disconnected components."""
    arg_map = ArgumentMap()
    
    # Create two disconnected nodes
    prop1 = Proposition(content="Claim 1")
    prop2 = Proposition(content="Claim 2")
    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)
    
    c1 = ClaimNode(label="C1", proposition_id=prop1.id)
    c2 = ClaimNode(label="C2", proposition_id=prop2.id)
    
    arg_map.add_claim(c1)
    arg_map.add_claim(c2)
    
    components = arg_map.connected_components()
    
    assert len(components) == 2


def test_is_acyclic_true() -> None:
    """Test acyclic graph detection."""
    arg_map = ArgumentMap()
    
    # Create simple chain (no cycles)
    prop1 = Proposition(content="Claim 1")
    prop2 = Proposition(content="Claim 2")
    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)
    
    c1 = ClaimNode(label="C1", proposition_id=prop1.id)
    c2 = ClaimNode(label="C2", proposition_id=prop2.id)
    
    arg_map.add_claim(c1)
    arg_map.add_claim(c2)
    arg_map.add_support_relation(from_label="C1", to_label="C2")
    
    assert arg_map.is_acyclic() is True


def test_longest_path() -> None:
    """Test finding longest path in graph."""
    arg_map = ArgumentMap()
    
    # Create chain: A1 -> C1 -> C2
    prop1 = Proposition(content="Claim 1")
    prop2 = Proposition(content="Claim 2")
    arg_map.add_proposition(prop1)
    arg_map.add_proposition(prop2)
    
    c1 = ClaimNode(label="C1", proposition_id=prop1.id)
    c2 = ClaimNode(label="C2", proposition_id=prop2.id)
    a1 = ArgumentNode(label="A1", gist="Argument 1")
    
    arg_map.add_claim(c1)
    arg_map.add_claim(c2)
    arg_map.add_argument(a1)
    
    arg_map.add_support_relation(from_label="A1", to_label="C1")
    arg_map.add_support_relation(from_label="C1", to_label="C2")
    
    path = arg_map.longest_path()
    
    # Path should have length 3 (includes all nodes)
    assert len(path) == 3
